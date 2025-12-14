import os
from dotenv import load_dotenv

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path 

env_path = Path(__file__).parent.parent.parent / ".env"

# Only load .env in development
# if os.getenv("RENDER") is None:  # Not running on Render
#     load_dotenv(dotenv_path=env_path)

load_dotenv(dotenv_path=env_path)
# load_dotenv()

class Settings:
    # FastAPI Config
    PROJECT_NAME: str = "Super Job Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    
    # Database Configuration (gunakan environment variables dari Render)
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "corporate")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
    
    # CORS Configuration
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

    database_url: str = os.getenv("DATABASE_URL", "")
    reminder_deadline_minutes: int = 60
    socketio_endpoint: str = "http://localhost:3001"
    socketio_namespace: str = "/"
    sentry_dsn: str | None = None
    monitoring_slow_ms: int = 400

    PROJECT_NAME: str = "Superjob API"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    JWT_SECRET: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ODOO_URL: str | None = None
    ODOO_DB: str | None = None
    ODOO_USER: str | None = None
    ODOO_PASSWORD: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()


