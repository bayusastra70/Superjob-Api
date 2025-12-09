from typing import Optional, Any
from app.schemas.response_schema import APIResponse, ErrorDetail

def success_response(data: Any = None) -> dict:
    """
    Create a success response with the standard format.
    
    Args:
        data: The data to include in the response
        
    Returns:
        dict: Formatted success response
    """
    return {
        "success": True,
        "data": data,
        "error": None
    }

def error_response(
    code: str,
    message: str,
    details: Optional[dict] = None
) -> dict:
    """
    Create an error response with the standard format.
    
    Args:
        code: Error code (e.g., "VALIDATION_ERROR", "NOT_FOUND")
        message: Error message
        details: Additional error details
        
    Returns:
        dict: Formatted error response
    """
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        }
    }

