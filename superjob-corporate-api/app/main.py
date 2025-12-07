from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.services.database import init_database
from app.core.config import settings
from app.api.routers import auth, health, candidate

from app.api import auth_router, health_router, candidate_router, chat_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
init_database()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
# app.include_router(auth.router)
# app.include_router(health.router)
# app.include_router(candidate.router, prefix=settings.API_V1_STR)

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(candidate_router, prefix=settings.API_V1_STR)
app.include_router(chat_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)