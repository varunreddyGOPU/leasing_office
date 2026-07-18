"""Ollama Cloud client. The API key lives ONLY in the OLLAMA_API_KEY env var —
never sent to the browser, never logged."""
from __future__ import annotations

from typing import AsyncIterator

import httpx

from app.config import settings


class OllamaUnavailable(Exception):
    """No API key configured or the upstream call failed."""


def _headers() -> dict:
    if not settings.ollama_api_key:
        raise OllamaUnavailable("OLLAMA_API_KEY is not configured")
    return {"Authorization": f"Bearer {settings.ollama_api_key}"}


async def stream_chat(messages: list[dict], model: str | None = None) -> AsyncIterator[str]:
    """Yield raw NDJSON lines from the Ollama Cloud streaming chat API."""
    payload = {"model": model or settings.ollama_model, "messages": messages, "stream": True}
    headers = _headers()
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream(
            "POST", settings.ollama_url, json=payload, headers=headers
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    yield line


async def chat_once(messages: list[dict], model: str | None = None) -> str:
    """Single non-streaming completion — used for lead extraction."""
    payload = {"model": model or settings.ollama_model, "messages": messages, "stream": False}
    headers = _headers()
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(settings.ollama_url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()["message"]["content"]
