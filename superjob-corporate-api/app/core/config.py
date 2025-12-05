
import os
from dotenv import load_dotenv

# Only load .env in development
if os.getenv("RENDER") is None:  # Not running on Render
    load_dotenv()

# load_dotenv()

class Settings:
    # FastAPI Config
    PROJECT_NAME: str = "Super Job Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = os.getenv("API_V1_STR", "/api/v1")
    
    # Database Configuration (gunakan environment variables dari Render)
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "super_job_db")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    
    # JWT Configuration
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
    
    # CORS Configuration
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

settings = Settings()