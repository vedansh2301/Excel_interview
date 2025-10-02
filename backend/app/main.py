from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import realtime, tools
from app.core.config import settings
from app.db import close_mongo_connection, connect_to_mongo
from app.services.storage import storage_service

app = FastAPI(title=settings.project_name)
app.include_router(tools.router, prefix=settings.api_v1_prefix)
app.include_router(realtime.router, prefix=settings.api_v1_prefix)

default_origins = {
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
}

if settings.cors_allow_origins:
    extra_origins = {origin.strip() for origin in settings.cors_allow_origins.split(",") if origin.strip()}
    allowed_origins = sorted(default_origins.union(extra_origins))
else:
    allowed_origins = sorted(default_origins)

origin_regex = settings.cors_allow_origin_regex or None

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=origin_regex,
)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "running"}


@app.on_event("startup")
async def on_startup() -> None:
    database = await connect_to_mongo()
    storage_service.configure(database)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    storage_service.configure(None)
    await close_mongo_connection()
