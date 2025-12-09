from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from typing import Union
from app.utils.response import error_response

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle validation errors and format them according to the custom response format.
    """
    errors = exc.errors()
    error_details = {}
    main_message = "Validation failed"
    
    for error in errors:
        # Get field name (skip "body" prefix if present)
        field_parts = [str(loc) for loc in error["loc"] if loc != "body"]
        field = ".".join(field_parts) if field_parts else "unknown"
        
        # Get error message
        message = error["msg"]
        
        # Format field name to be more readable (e.g., "title" -> "Title")
        formatted_field = field.split(".")[-1].replace("_", " ").title() if field else "Field"
        
        # Create user-friendly message
        if "required" in message.lower() or "field required" in message.lower():
            user_message = f"{formatted_field} is required"
        else:
            user_message = f"{formatted_field}: {message}"
        
        error_details[field] = message
        
        # Use first error as main message
        if main_message == "Validation failed":
            main_message = user_message
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(
            code="VALIDATION_ERROR",
            message=main_message,
            details=error_details
        )
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions and format them according to the custom response format.
    """
    status_code = exc.status_code
    detail = exc.detail
    
    # Map common status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_SERVER_ERROR",
    }
    
    error_code = error_code_map.get(status_code, "HTTP_ERROR")
    
    # If detail is a string, use it as message
    if isinstance(detail, str):
        message = detail
    elif isinstance(detail, dict):
        message = detail.get("message", "An error occurred")
    else:
        message = "An error occurred"
    
    return JSONResponse(
        status_code=status_code,
        content=error_response(
            code=error_code,
            message=message,
            details={}
        )
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle general exceptions and format them according to the custom response format.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            code="INTERNAL_SERVER_ERROR",
            message="An internal server error occurred",
            details={}
        )
    )

