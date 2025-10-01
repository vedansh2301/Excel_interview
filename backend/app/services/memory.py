from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis
from redis.exceptions import RedisError

from app.core.config import settings


class MemoryService:
    """Handles session-context persistence in Redis."""

    def __init__(self) -> None:
        self._client = None if not settings.redis_url else redis.from_url(settings.redis_url, decode_responses=True)

    async def get_session_context(self, session_id: str) -> dict[str, Any] | None:
        if self._client is None:
            return None
        try:
            raw = await self._client.get(self._session_context_key(session_id))
        except RedisError:
            self._client = None
            return None
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    async def set_session_context(self, session_id: str, context: dict[str, Any]) -> None:
        if self._client is None:
            return
        try:
            await self._client.set(self._session_context_key(session_id), json.dumps(context))
        except RedisError:
            self._client = None

    async def append_transcript_turn(self, session_id: str, turn: dict[str, Any]) -> None:
        if self._client is None:
            return
        try:
            await self._client.rpush(self._transcript_key(session_id), json.dumps(turn))
        except RedisError:
            self._client = None

    async def get_recent_transcript(self, session_id: str, limit: int = 10) -> list[dict[str, Any]]:
        if self._client is None:
            return []
        try:
            raw_entries = await self._client.lrange(self._transcript_key(session_id), -limit, -1)
        except RedisError:
            self._client = None
            return []
        result: list[dict[str, Any]] = []
        for raw in raw_entries:
            try:
                result.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
        return result

    def _session_context_key(self, session_id: str) -> str:
        return f"session:{session_id}:context"

    def _transcript_key(self, session_id: str) -> str:
        return f"session:{session_id}:transcript"


memory_service = MemoryService()
