from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

CURRENT_FILE = Path(__file__).resolve()
BACKEND_DIR = CURRENT_FILE.parents[2]
PROJECT_ROOT = CURRENT_FILE.parents[3]

ENV_PATHS = [PROJECT_ROOT / ".env", BACKEND_DIR / ".env"]
ENV_FILE = next((path for path in ENV_PATHS if path.exists()), None)


class Settings(BaseSettings):
    api_v1_prefix: str = "/api/v1"
    project_name: str = "Agentic Interview Platform"
    mongo_dsn: str = "mongodb://localhost:27017"
    mongo_db_name: str = "interview"
    redis_url: str = ""
    s3_bucket: str = "interview-agent-artifacts"
    openai_api_key: str = ""
    realtime_model: str = "gpt-4o-realtime-preview"
    default_model: str = "gpt-4o-mini"
    default_verbosity: str = "medium"
    default_reasoning_effort: str = "medium"
    hunter_api_key: str = ""
    cors_allow_origins: str = ""

    if ENV_FILE is not None:
        model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_file_encoding="utf-8")
    else:
        model_config = SettingsConfigDict()


settings = Settings()
