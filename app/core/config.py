from dotenv import load_dotenv

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import List

import os

env_path = Path(__file__).parent.parent.parent / ".env"

if os.getenv("RENDER") is None:  # Not running on Render
    load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    # FastAPI Config
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "")
    VERSION: str = os.getenv("VERSION", "")
    API_V1_STR: str = os.getenv("API_V1_STR", "")
    API_V1_PREFIX: str = os.getenv("API_V1_STR", "")

    # Database Configuration
    DB_HOST: str = os.getenv("DB_HOST", "")
    DB_PORT: str = os.getenv("DB_PORT", "")
    DB_NAME: str = os.getenv("DB_NAME", "")
    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "")
    JWT_EXPIRE_MINUTES: int = int( os.getenv("JWT_EXPIRE_MINUTES", ""))

    # CORS Configuration
    CORS_ORIGINS: List[str] = ["*"]

    # App Config
    reminder_deadline_minutes: int = 60
    socketio_endpoint: str = "http://localhost:3001"
    socketio_namespace: str = "/"
    sentry_dsn: str | None = None
    monitoring_slow_ms: int = 400

    # Odoo Config (optional)
    ODOO_URL: str | None = None
    ODOO_DB: str | None = None
    ODOO_USER: str | None = None
    ODOO_PASSWORD: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
