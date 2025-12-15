from dotenv import load_dotenv

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import List

env_path = Path(__file__).parent.parent.parent / ".env"

# Load .env file
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    # FastAPI Config
    PROJECT_NAME: str = "Superjob API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    API_V1_PREFIX: str = "/api/v1"

    # Database Configuration
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "corporate"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DATABASE_URL: str = ""

    # JWT Configuration
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30

    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

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
