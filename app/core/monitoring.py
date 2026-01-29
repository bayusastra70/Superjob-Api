import time
import uuid
import json
import sys
import traceback
import logging
import base64
from typing import Callable, Any, Dict, Optional
from fastapi import FastAPI, Request, Response
from loguru import logger

from app.core.config import settings

async def get_body(request: Request) -> bytes:
    body = await request.body()
    # We need to re-set the body for FastAPI to read it again
    # But BaseHTTPMiddleware has issues with this. Using a more robust approach:
    return body


def redact_payload(payload: Any) -> Any:
    """Redact sensitive info and summarize large arrays/binary data. Returns dict/list, not JSON string."""
    sensitive_keys = {"password", "current_password", "new_password", "token", "secret", "authorization", "access_token", "refresh_token"}
    
    def _process(obj):
        if isinstance(obj, dict):
            return {k: ("[REDACTED]" if k.lower() in sensitive_keys else _process(v)) for k, v in obj.items()}
        elif isinstance(obj, list):
            if len(obj) >= 10:
                return f"[Array({len(obj)})]"
            return [_process(v) for v in obj]
        return obj

    try:
        if isinstance(payload, bytes):
            try:
                payload = payload.decode("utf-8")
                data = json.loads(payload)
                return _process(data)
            except (UnicodeDecodeError, json.JSONDecodeError):
                return "[BINARY_OR_ENCODED_DATA]"
        
        if isinstance(payload, str):
            try:
                data = json.loads(payload)
                return _process(data)
            except json.JSONDecodeError:
                return f"[TEXT_CONTENT: {payload[:50]}...]" if len(payload) > 50 else payload
        
        return _process(payload)
    except Exception:
        return "[UNPARSEABLE_PAYLOAD]"


async def capture_request_summary(request: Request) -> Any:
    """Summarize request body based on content type. Returns dict or string.
    
    NOTE: We only read JSON bodies here because they can be re-set via _receive.
    Form-data streams cannot be re-read, so we just log the content-type.
    """
    content_type = request.headers.get("content-type", "")
    
    if "application/json" in content_type:
        try:
            body = await request.body()
            return redact_payload(body)
        except Exception:
            return "[ERROR_READING_JSON_BODY]"
    
    # For form-data, we cannot read the body without consuming it
    # Just log that it's form-data (the middleware will handle re-setting JSON bodies)
    if "multipart/form-data" in content_type:
        return "[multipart/form-data]"
    
    if "application/x-www-form-urlencoded" in content_type:
        return "[form-urlencoded]"
            
    return f"[{content_type or 'no-content-type'}]"


def register_structured_logging_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def structured_logging_middleware(request: Request, call_next: Callable):
        # Skip logging for noise endpoints
        skip_paths = ["/metrics", "/docs", "/redoc", "/openapi.json", "/health"]
        if any(request.url.path == path or request.url.path.endswith(path) for path in skip_paths):
            return await call_next(request)
        
        start_time = time.perf_counter()
        request_id = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:8]}")
        
        # 1. Capture Request Payload (Redacted and Summarized)
        request_payload = await capture_request_summary(request)
        
        # BaseHTTPMiddleware hack to allow reading body again if it was a stream
        if "application/json" in request.headers.get("content-type", ""):
            body = await request.body()
            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive

        error_data = None
        response_payload = ""
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            # Capture Response Payload (Redacted)
            # Note: capturing response body in middleware is expensive and needs care
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Since we consumed the iterator, we must return a new one
            response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
            
            response_payload = redact_payload(response_body.decode("utf-8", errors="ignore"))

            # Log level transition
            log_level = "INFO"
            if 400 <= status_code < 500:
                log_level = "WARNING"
            elif status_code >= 500:
                log_level = "ERROR"

            # 2. Emit Single Summary Log
            user_id = getattr(request.state, "user_id", None)
            
            logger.log(
                log_level,
                "HTTP Request Processed",
                request_id=request_id,
                user_id=user_id,
                http={
                    "method": request.method,
                    "path": request.url.path,
                    "status": status_code,
                    "latency_ms": round(elapsed_ms, 2),
                    "ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent")
                },
                payload={
                    "request": request_payload,
                    "response": response_payload
                }
            )
            
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            user_id = getattr(request.state, "user_id", None)

            logger.error(
                "Unhandled exception occurred",
                request_id=request_id,
                user_id=user_id,
                http={
                    "method": request.method,
                    "path": request.url.path,
                    "status": 500,
                    "latency_ms": round(elapsed_ms, 2),
                    "ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent")
                },
                payload={
                    "request": request_payload,
                    "response": '{"error": "internal server error"}'
                },
                error={
                    "message": str(e),
                    "code": "INTERNAL_SERVER_ERROR",
                    "stack_trace": "".join(traceback.format_exception(type(e), e, e.__traceback__))
                }
            )
            raise e


def register_metrics_auth_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def metrics_auth_middleware(request: Request, call_next: Callable):
        if request.url.path == "/metrics":
            # Skip auth if credentials not configured
            if not settings.METRICS_USERNAME or not settings.METRICS_PASSWORD:
                return await call_next(request)

            auth_header = request.headers.get("Authorization")
            expected = f"{settings.METRICS_USERNAME}:{settings.METRICS_PASSWORD}"
            expected_b64 = base64.b64encode(expected.encode()).decode()
            if auth_header != f"Basic {expected_b64}":
                return Response(
                    status_code=401,
                    content="Unauthorized",
                    headers={"WWW-Authenticate": 'Basic realm="Metrics"'}
                )

        return await call_next(request)

# Helper to easily log business events
def log_business_event(message: str, event: str, context: Optional[Dict[str, Any]] = None, user_id: Any = None):
    logger.info(
        message,
        event=event,
        user_id=user_id,
        context=context or {}
    )


def patch_loguru():
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            frame, depth = logging.currentframe(), 2
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    def sink(message):
        record = message.record
        extra = record["extra"]
        
        # Skip uvicorn access logs for noise endpoints
        msg = record["message"]
        skip_paths = ["/metrics", "/docs", "/redoc", "/openapi.json"]
        if any(f'"{path} ' in msg or f'{path} ' in msg for path in skip_paths):
            return
        
        timestamp = record["time"].strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        
        log_data = {
            "timestamp": timestamp,
            "level": record["level"].name,
            "service": settings.SERVICE_NAME,
            "environment": settings.ENVIRONMENT,
            "request_id": extra.get("request_id"),
            "user_id": extra.get("user_id"),
            "message": record["message"],
            "logger_name": extra.get("name", record["name"]) # Identify logger source
        }
        
        if "http" in extra:
            log_data["http"] = extra["http"]
        
        if "payload" in extra:
            log_data["payload"] = extra["payload"]
        
        if extra.get("error"):
            log_data["error"] = extra["error"]
        
        if "event" in extra:
            log_data["event"] = extra["event"]

        # Other context
        reserved = ["request_id", "user_id", "http", "payload", "error", "event"]
        other_context = {k: v for k, v in extra.items() if k not in reserved}
        if other_context:
            log_data["context"] = other_context

        sys.stdout.write(json.dumps(log_data) + "\n")

    logger.remove()
    # Use INFO level for cleaner logs (DEBUG is too verbose with httpx/multipart)
    logger.add(sink, level="INFO")
    logging.basicConfig(handlers=[InterceptHandler()], level=logging.INFO, force=True)
    
    # Intercept uvicorn loggers so they use our structured format
    # Note: We disable uvicorn.access and uvicorn.error since our middleware handles requests and exceptions
    for uvicorn_logger_name in ["uvicorn"]:
        uvicorn_logger = logging.getLogger(uvicorn_logger_name)
        uvicorn_logger.handlers = [InterceptHandler()]
        uvicorn_logger.propagate = False
    
    # Disable uvicorn access logger (we have our own structured request logging)
    logging.getLogger("uvicorn.access").disabled = True
    # Disable uvicorn error logger to prevent duplicates (middleware handles exceptions)
    logging.getLogger("uvicorn.error").disabled = True
    
    # Silence noisy third-party loggers
    noisy_loggers = [
        "httpx", "httpcore", "httpcore.http11", "httpcore.connection",
        "multipart", "python_multipart", "multipart.multipart",
        "hpack", "h2", "asyncio"
    ]
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

patch_loguru()
