from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Superjob API"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = Field(..., description="Database connection URL")
    JWT_SECRET: str = Field(..., description="Secret key for JWT tokens")
    JWT_ALGORITHM: str = "HS256"
    ODOO_URL: str | None = None
    ODOO_DB: str | None = None
    ODOO_USER: str | None = None
    ODOO_PASSWORD: str | None = None

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()  # type: ignore[call-arg]