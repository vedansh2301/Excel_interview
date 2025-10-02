from __future__ import annotations

import httpx
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.core.config import settings

router = APIRouter(prefix="/realtime", tags=["realtime"])
logger = logging.getLogger(__name__)


@router.options("/session-token")
async def options_session_token() -> JSONResponse:
    return JSONResponse(status_code=200, content={})


@router.post("/session-token")
async def create_realtime_session_token() -> dict[str, str]:
    api_key = settings.openai_api_key
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    payload = {
        "session": {
            "type": "realtime",
            "model": settings.realtime_model,
            "audio": {
                "output": {"voice": "alloy"},
            },
            "instructions": (
                "You are an English-speaking Excel interviewer. Ask exactly one focused question at a time. "
                "After you ask a question, remain silent until the candidate responds. "
                "When the candidate answers, reply with a single short acknowledgement such as 'Thanks, let’s move on to the next topic.' and then wait for the next tool-provided question. "
                "Do not chain follow-up prompts inside the same turn and do not keep elaborating once the question has been answered."
            ),
        }
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/realtime/client_secrets",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except httpx.HTTPError as exc:
        logger.exception("Failed to contact OpenAI Realtime API")
        raise HTTPException(status_code=502, detail="Failed to contact OpenAI Realtime API") from exc

    if response.status_code != 200:
        content_type = response.headers.get("content-type", "")
        detail = response.json() if content_type.startswith("application/json") else response.text
        logger.error("OpenAI Realtime API error %s: %s", response.status_code, detail)
        raise HTTPException(status_code=response.status_code, detail=detail)

    data = response.json()
    client_secret = data.get("value", "")
    session = data.get("session", {})
    expires_at = data.get("expires_at")
    expires_at_str = str(expires_at) if expires_at is not None else ""
    return {
        "client_secret": client_secret,
        "session_id": session.get("id", ""),
        "expires_at": expires_at_str,
    }
