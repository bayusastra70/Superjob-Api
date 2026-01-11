

from fastapi import HTTPException, status
from typing import Optional, Any

class CustomHTTPException(HTTPException):
    def __init__(
        self,
        status_code: int,
        message: str,
        detail: Optional[Any] = None,
        headers: Optional[dict] = None
    ):
        # Format response sesuai BaseResponse
        response_detail = {
            "code": status_code,
            "isSuccess": False,
            "message": message,
            "data": None
        }
        
        super().__init__(
            status_code=status_code,
            detail=response_detail,
            headers=headers
        )

# Specialized exceptions
class UnauthorizedException(CustomHTTPException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message
        )

class NotFoundException(CustomHTTPException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"{resource} not found"
        )

class BadRequestException(CustomHTTPException):
    def __init__(self, message: str = "Bad Request"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message
        )