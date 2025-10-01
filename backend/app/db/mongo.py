from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings


_client: AsyncIOMotorClient | None = None
_database: AsyncIOMotorDatabase | None = None


async def connect_to_mongo() -> Optional[AsyncIOMotorDatabase]:
    global _client, _database
    if not settings.mongo_dsn:
        _client = None
        _database = None
        return None
    try:
        _client = AsyncIOMotorClient(settings.mongo_dsn, serverSelectionTimeoutMS=500)
        await _client.admin.command("ping")
    except Exception:
        _client = None
        _database = None
        return None
    _database = _client[settings.mongo_db_name]
    return _database


async def close_mongo_connection() -> None:
    global _client, _database
    if _client is not None:
        _client.close()
    _client = None
    _database = None


def get_database() -> AsyncIOMotorDatabase:
    if _database is None:
        raise RuntimeError("Mongo database is not initialized. Call connect_to_mongo first.")
    return _database
