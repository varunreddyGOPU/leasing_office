import json

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app import models
from app.db import SessionLocal, get_db
from app.ratelimit import rate_limit
from app.services import ollama
from app.services.chatbot import (
    EXTRACTION_INSTRUCTION,
    FALLBACK_MESSAGE,
    build_system_prompt,
    parse_extracted,
)
from app.services.leads import upsert_lead

router = APIRouter(prefix="/api", tags=["chat"])

MAX_CONTEXT_MESSAGES = 20


class ChatRequest(BaseModel):
    session_id: int | None = None
    message: str = Field(..., min_length=1, max_length=2000)


class ExtractRequest(BaseModel):
    session_id: int


class ExtractResponse(BaseModel):
    session_id: int
    saved: bool
    has_contact: bool
    lead_id: int | None = None


def _append_assistant_turn(session_id: int, text: str) -> None:
    # Fresh DB session: the request-scoped one may be closed by the time the
    # stream finishes.
    with SessionLocal() as db:
        session = db.get(models.ChatSession, session_id)
        if session is None:
            return
        transcript = list(session.transcript_json or [])
        transcript.append({"role": "assistant", "content": text})
        session.transcript_json = transcript
        db.commit()


@router.post("/chat", dependencies=[Depends(rate_limit("chat", per_minute=20))])
async def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    session = db.get(models.ChatSession, payload.session_id) if payload.session_id else None
    if session is None:
        session = models.ChatSession(transcript_json=[])
        db.add(session)
        db.flush()

    transcript = list(session.transcript_json or [])
    transcript.append({"role": "user", "content": payload.message})
    session.transcript_json = transcript
    session_id = session.id

    system_prompt = build_system_prompt(db)
    llm_messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]}
        for m in transcript[-MAX_CONTEXT_MESSAGES:]
        if m.get("role") in ("user", "assistant")
    ]
    db.commit()  # persist the user turn before streaming begins

    async def event_stream():
        assistant_text = ""
        try:
            async for line in ollama.stream_chat(llm_messages):
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                delta = chunk.get("message", {}).get("content", "")
                if delta:
                    assistant_text += delta
                    yield f"data: {json.dumps({'delta': delta})}\n\n"
                if chunk.get("done"):
                    break
        except (ollama.OllamaUnavailable, httpx.HTTPError):
            assistant_text = FALLBACK_MESSAGE
            yield f"data: {json.dumps({'delta': FALLBACK_MESSAGE, 'fallback': True})}\n\n"
        _append_assistant_turn(session_id, assistant_text)
        yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post(
    "/chat/extract",
    response_model=ExtractResponse,
    dependencies=[Depends(rate_limit("chat_extract", per_minute=30))],
)
async def extract(payload: ExtractRequest, db: Session = Depends(get_db)) -> ExtractResponse:
    session = db.get(models.ChatSession, payload.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown chat session.")

    transcript = [
        m for m in (session.transcript_json or []) if m.get("role") in ("user", "assistant")
    ]
    if not transcript:
        return ExtractResponse(session_id=session.id, saved=False, has_contact=False)

    conversation = "\n".join(f"{m['role']}: {m['content']}" for m in transcript)
    try:
        raw = await ollama.chat_once(
            [
                {"role": "system", "content": EXTRACTION_INSTRUCTION},
                {"role": "user", "content": conversation},
            ]
        )
    except (ollama.OllamaUnavailable, httpx.HTTPError):
        return ExtractResponse(session_id=session.id, saved=False, has_contact=False)

    data = parse_extracted(raw)
    if data:
        session.extracted_json = {
            **data,
            "move_in_date": data["move_in_date"].isoformat() if data.get("move_in_date") else None,
        }
    has_contact = bool(data.get("email") or data.get("phone")) if data else False

    lead_id = None
    if has_contact:
        lead = upsert_lead(
            db,
            email=data.get("email"),
            phone=data.get("phone"),
            source="chatbot",
            name=data.get("name"),
            desired_bedrooms=data.get("desired_bedrooms"),
            move_in_date=data.get("move_in_date"),
            budget=data.get("budget"),
            pets=data.get("pets"),
            notes=data.get("notes"),
        )
        session.lead_id = lead.id
        lead_id = lead.id
    db.commit()

    return ExtractResponse(
        session_id=session.id, saved=has_contact, has_contact=has_contact, lead_id=lead_id
    )
