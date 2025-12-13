import time
from typing import Callable

from fastapi import FastAPI, Request
from loguru import logger

from app.core.config import settings

try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None


def init_sentry() -> None:
    if settings.sentry_dsn and sentry_sdk:
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.2)
        logger.info("Sentry initialized")


def register_timing_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def timing_middleware(request: Request, call_next: Callable):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Log slow requests
        if elapsed_ms > settings.monitoring_slow_ms:
            logger.warning(
                "Slow request detected",
                path=request.url.path,
                method=request.method,
                elapsed_ms=round(elapsed_ms, 2),
                status_code=response.status_code,
            )
        return response
