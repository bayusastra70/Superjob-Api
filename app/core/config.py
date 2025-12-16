import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent.parent / ".env"

# Only load .env in development
if os.getenv("RENDER") is None:  # Not running on Render
    load_dotenv(dotenv_path=env_path)


class Settings:
    # FastAPI Config
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Super Job Backend")
    VERSION: str = os.getenv("VERSION", "1.0.0")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    API_V1_PREFIX: str = os.getenv("API_V1_STR", "/api/v1") 

    # Database Configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "corporate")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

    CORS_ORIGINS: list = ["*"]

    # App Config
    reminder_deadline_minutes: int = 60
    socketio_endpoint: str = "http://localhost:3001"
    socketio_namespace: str = "/"
    sentry_dsn: str | None = None
    monitoring_slow_ms: int = 400

    # Odoo Config (optional)
    ODOO_URL: str | None = os.getenv("ODOO_URL")
    ODOO_DB: str | None = os.getenv("ODOO_DB")
    ODOO_USER: str | None = os.getenv("ODOO_USER")
    ODOO_PASSWORD: str | None = os.getenv("ODOO_PASSWORD")


settings = Settings()