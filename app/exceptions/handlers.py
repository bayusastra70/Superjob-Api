
from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle validation errors in BaseResponse format
    """
    errors = exc.errors()
    error_messages = []
    
    for error in errors:
        # Get field path
        field_parts = [str(loc) for loc in error["loc"] if loc != "body"]
        field = ".".join(field_parts) if field_parts else "request"
        
        # Format field name
        formatted_field = field.split(".")[-1].replace("_", " ").title() if field else "Field"
        
        # Create user-friendly message
        message = error["msg"]
        if "required" in message.lower():
            user_message = f"{formatted_field} is required"
        elif "not a valid" in message.lower():
            user_message = f"{formatted_field} is invalid"
        else:
            user_message = f"{formatted_field}: {message}"
        
        error_messages.append(user_message)
    
    # Combine messages
    if error_messages:
        main_message = f"Validation error: {', '.join(error_messages)}"
    else:
        main_message = "Validation error"
    
    # Return in BaseResponse format
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "is_success": False,
            "message": main_message,
            "data": None
        }
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    status_code = exc.status_code
    
    # Extract message - PERBAIKAN: CustomHTTPException pakai lowercase
    if isinstance(exc.detail, dict):
        # Check if already in BaseResponse format (LOWERCASE)
        if "message" in exc.detail:  # ✅ Cari lowercase "message"
            message = exc.detail["message"]
        elif "Message" in exc.detail:  # Fallback untuk uppercase
            message = exc.detail["Message"]
        else:
            message = str(exc.detail)
    else:
        message = str(exc.detail) if exc.detail else "An error occurred"
    
    # Check if already in correct format (LOWERCASE)
    if isinstance(exc.detail, dict) and "code" in exc.detail:  # ✅ Cari lowercase "code"
        # Already in BaseResponse format
        return JSONResponse(
            status_code=status_code,
            content=exc.detail,  # ✅ exc.detail dari CustomHTTPException sudah lowercase
            headers=exc.headers
        )
    
    # Convert to BaseResponse format
    return JSONResponse(
        status_code=status_code,
        content={
            "code": status_code,
            "is_success": False,
            "message": message,
            "data": None
        },
        headers=exc.headers
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle general exceptions in BaseResponse format
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    # Check if it's HTTPException
    if isinstance(exc, HTTPException):
        return await http_exception_handler(request, exc)
    
    # Return in BaseResponse format
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "is_success": False,
            "message": "Internal Server Error",
            "data": None
        }
    )