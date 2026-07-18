"""Chatbot tests — Ollama is mocked; no network or API key needed."""
import json

from app.services import ollama
from app.services.chatbot import parse_extracted
from tests.test_smoke import client


def _sse_events(body: str) -> list[dict]:
    return [
        json.loads(line[len("data: "):])
        for line in body.splitlines()
        if line.startswith("data: ")
    ]


def test_chat_streams_and_persists(monkeypatch):
    async def fake_stream(messages, model=None):
        # System prompt must carry injected DB facts.
        assert messages[0]["role"] == "system"
        assert "Ridgeline Assistant" in messages[0]["content"]
        assert "CURRENT AVAILABILITY" in messages[0]["content"]
        assert "The Cedar" in messages[0]["content"]
        for token in ["Hello", " from", " Ridgeline!"]:
            yield json.dumps({"message": {"role": "assistant", "content": token}, "done": False})
        yield json.dumps({"message": {"role": "assistant", "content": ""}, "done": True})

    monkeypatch.setattr(ollama, "stream_chat", fake_stream)

    r = client.post("/api/chat", json={"message": "Hi, do you have 2 bedrooms?"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    events = _sse_events(r.text)
    deltas = "".join(e.get("delta", "") for e in events)
    assert deltas == "Hello from Ridgeline!"
    done = events[-1]
    assert done["done"] is True
    session_id = done["session_id"]

    # Second turn continues the same session and transcript.
    r2 = client.post(
        "/api/chat", json={"session_id": session_id, "message": "What about pets?"}
    )
    assert r2.status_code == 200
    assert _sse_events(r2.text)[-1]["session_id"] == session_id

    from app import models
    from app.db import SessionLocal

    with SessionLocal() as db:
        session = db.get(models.ChatSession, session_id)
        roles = [m["role"] for m in session.transcript_json]
        assert roles == ["user", "assistant", "user", "assistant"]


def test_chat_fallback_without_api_key():
    # No monkeypatch: ollama_api_key is empty in tests -> OllamaUnavailable.
    r = client.post("/api/chat", json={"message": "Hello?"})
    assert r.status_code == 200
    events = _sse_events(r.text)
    assert any(e.get("fallback") for e in events)
    assert "248-377-2680" in "".join(e.get("delta", "") for e in events)
    assert events[-1]["done"] is True


def test_parse_extracted_defensively():
    fenced = """Here you go:
```json
{"name": "Pat Chat", "phone": "248-555-0700", "email": "pat@example.com",
 "desired_bedrooms": "2", "move_in_date": "2026-10-01", "budget": "$1,600",
 "pets": "1 dog", "notes": null}
```"""
    data = parse_extracted(fenced)
    assert data["name"] == "Pat Chat"
    assert data["desired_bedrooms"] == 2
    assert str(data["move_in_date"]) == "2026-10-01"
    assert data["budget"] == 1600.0

    assert parse_extracted("no json here at all") == {}
    assert parse_extracted('{"email": "not-an-email"}')["email"] is None
    assert parse_extracted('{"desired_bedrooms": 9, "budget": -5}') == {
        "name": None, "phone": None, "email": None, "pets": None, "notes": None,
        "desired_bedrooms": None, "move_in_date": None, "budget": None,
    }


def test_extract_endpoint_upserts_chatbot_lead(monkeypatch):
    async def fake_stream(messages, model=None):
        yield json.dumps({"message": {"role": "assistant", "content": "Sure!"}, "done": True})

    async def fake_once(messages, model=None):
        assert "strict JSON" in messages[0]["content"]
        return (
            '```json\n{"name": "Chat Lead", "phone": null, "email": "chat.lead@example.com",'
            ' "desired_bedrooms": 2, "move_in_date": "2026-11-01", "budget": 1650,'
            ' "pets": "1 cat", "notes": "asked about pool"}\n```'
        )

    monkeypatch.setattr(ollama, "stream_chat", fake_stream)
    monkeypatch.setattr(ollama, "chat_once", fake_once)

    r = client.post("/api/chat", json={"message": "I want a 2 bed, I'm chat.lead@example.com"})
    session_id = _sse_events(r.text)[-1]["session_id"]

    r = client.post("/api/chat/extract", json={"session_id": session_id})
    assert r.status_code == 200
    body = r.json()
    assert body["saved"] is True and body["has_contact"] is True

    from app import models
    from app.db import SessionLocal

    with SessionLocal() as db:
        lead = db.get(models.Lead, body["lead_id"])
        assert lead.source == "chatbot"
        assert lead.email == "chat.lead@example.com"
        assert lead.desired_bedrooms == 2
        session = db.get(models.ChatSession, session_id)
        assert session.lead_id == lead.id
        assert session.extracted_json["name"] == "Chat Lead"


def test_extract_no_contact_no_lead(monkeypatch):
    async def fake_stream(messages, model=None):
        yield json.dumps({"message": {"role": "assistant", "content": "Hi!"}, "done": True})

    async def fake_once(messages, model=None):
        return '{"name": null, "phone": null, "email": null, "desired_bedrooms": 1}'

    monkeypatch.setattr(ollama, "stream_chat", fake_stream)
    monkeypatch.setattr(ollama, "chat_once", fake_once)

    r = client.post("/api/chat", json={"message": "just browsing"})
    session_id = _sse_events(r.text)[-1]["session_id"]
    r = client.post("/api/chat/extract", json={"session_id": session_id})
    assert r.json() == {
        "session_id": session_id, "saved": False, "has_contact": False, "lead_id": None,
    }
