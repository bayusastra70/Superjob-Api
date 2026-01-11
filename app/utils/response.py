from typing import Optional, Any
from fastapi import status
from app.schemas.response import BaseResponse
from app.exceptions.custom_exceptions import CustomHTTPException


def success_response(
    data: Optional[Any] = None,
    message: str = "Success",
    code: int = status.HTTP_200_OK
) -> BaseResponse:
    """
    Helper untuk membuat success response berdasarkan BaseResponse
    """
    return BaseResponse(
        code=code,
        is_success=True,
        message=message,
        data=data
    )

def error_response(
    message: str = "Error",
    code: int = status.HTTP_400_BAD_REQUEST,
    raise_exception: bool = True
) -> BaseResponse:
    """
    Helper untuk membuat error response berdasarkan BaseResponse
    Data selalu None untuk error responses
    """
    if raise_exception:
        # RAISE exception dan STOP execution
        from app.exceptions.custom_exceptions import CustomHTTPException
        raise CustomHTTPException(
            status_code=code,
            message=message
        )
    else:
        # RETURN response object
        return BaseResponse(
            code=code,
            is_success=False,
            message=message,
            data=None
        )

def unauthorized_response(
    message: str = "Unauthorized",
    raise_exception: bool = True
) -> BaseResponse:
    """Helper untuk 401 Unauthorized"""
    return error_response(
        message=message,
        code=status.HTTP_401_UNAUTHORIZED,
        raise_exception=raise_exception
    )

def not_found_response(
    message: str = "",
    raise_exception: bool = True
) -> BaseResponse:
    """Helper untuk 404 Not Found"""
    return error_response(
        message=message,
        code=status.HTTP_404_NOT_FOUND,
        raise_exception=raise_exception
    )

def bad_request_response(
    message: str = "Bad Request",
    raise_exception: bool = True
) -> BaseResponse:
    """Helper untuk 400 Bad Request"""
    return error_response(
        message=message,
        code=status.HTTP_400_BAD_REQUEST,
        raise_exception=raise_exception
    )

def forbidden_response(
    message: str = "Forbidden",
    raise_exception: bool = True
) -> BaseResponse:
    """Helper untuk 403 Forbidden"""
    return error_response(
        message=message,
        code=status.HTTP_403_FORBIDDEN,
        raise_exception=raise_exception
    )

def internal_server_error_response(
    message: str = "Internal Server Error",
    raise_exception: bool = True
) -> BaseResponse:
    """Helper untuk 500 Internal Server Error"""
    return error_response(
        message=message,
        code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        raise_exception=raise_exception
    )

def created_response(
    data: Optional[Any] = None,
    message: str = "Created successfully"
) -> BaseResponse:
    """Helper untuk 201 Created"""
    return BaseResponse(
        code=status.HTTP_201_CREATED,
        is_success=True,
        message=message,
        data=data
    )

def no_content_response(
    message: str = "No content"
) -> BaseResponse:
    """Helper untuk 204 No Content"""
    return BaseResponse(
        code=status.HTTP_204_NO_CONTENT,
        is_success=True,
        message=message,
        data=None
    )

def validation_error_response(
    errors: list,
    raise_exception: bool = True
) -> BaseResponse:
    """
    Helper untuk validation errors
    errors: list of error dicts from RequestValidationError
    """
    error_messages = []
    for error in errors:
        field = " -> ".join(str(loc) for loc in error['loc'])
        error_messages.append(f"{field}: {error['msg']}")
    
    return error_response(
        message=f"Validation error: {', '.join(error_messages)}",
        code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        raise_exception=raise_exception
    )
