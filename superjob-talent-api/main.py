from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from app.api.v1.router import api_router
from app.core.config import settings
from app.exceptions import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
)

# Sesuaikan origins dengan domain Next.js di Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # TODO: ganti ke domain tertentu di production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore
app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore
app.add_exception_handler(Exception, general_exception_handler)  # type: ignore

app.include_router(api_router, prefix=settings.API_V1_PREFIX)
@app.get("/")
def health():
    return {"status": "ok", "service": "superjob-api"}