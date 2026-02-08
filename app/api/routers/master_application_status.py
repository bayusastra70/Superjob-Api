from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.core.security import get_current_user
from app.schemas.user import UserResponse
from app.schemas.response import BaseResponse
from app.utils.response import (
    success_response,
    unauthorized_response,
    internal_server_error_response,
    not_found_response,
    bad_request_response,
    created_response
)

from app.schemas.master_application_status import (
    ApplicationStatusCreate,
    ApplicationStatusUpdate,
    ApplicationStatusResponse,
    ApplicationStatusListResponse
)
from app.services.master_application_status_service import master_application_status_service

router = APIRouter(prefix="/master/application-statuses", tags=["Master Application Statuses"])


@router.get(
    "/",
    response_model=BaseResponse[ApplicationStatusListResponse],
    summary="Get all application statuses"
)
async def get_application_statuses(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get list of all application statuses sorted by display_order.
    """
    try:
        statuses = await master_application_status_service.get_all_application_statuses()
        
        return success_response(
            data=ApplicationStatusListResponse(
                items=statuses,
                total=len(statuses)
            ),
        )
    except Exception as e:
        logger.error(f"Error getting application statuses: {str(e)}")
        raise 


@router.get(
    "/{status_id}",
    response_model=BaseResponse[ApplicationStatusResponse],
    summary="Get application status by ID"
)
async def get_application_status(
    status_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get specific application status by ID.
    """
    try:
        status_obj = await master_application_status_service.get_application_status_by_id(status_id)
        
        if not status_obj:
            return not_found_response() 
        
        return success_response(
            data=status_obj
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting application status {status_id}: {str(e)}")
        raise 


@router.get(
    "/code/{code}",
    response_model=BaseResponse[ApplicationStatusResponse],
    summary="Get application status by code"
)
async def get_application_status_by_code(
    code: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get application status by code.
    """
    try:
        status_obj = await master_application_status_service.get_application_status_by_code(code)
        
        if not status_obj:
            raise not_found_response()
        
        return success_response(
            data=status_obj
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting application status by code {code}: {str(e)}")
        raise 


@router.post(
    "/",
    response_model=BaseResponse[ApplicationStatusResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create new application status"
)
async def create_application_status(
    status_data: ApplicationStatusCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new application status.
    """
    try:
        new_status = await master_application_status_service.create_application_status(status_data)
        
        if not new_status:
            return bad_request_response()
        
        return success_response(
            data=new_status,
        )
    except ValueError as e:
        return bad_request_response(message=str(e))
    except Exception as e:
        logger.error(f"Error creating application status: {str(e)}")
        raise 


@router.put(
    "/{status_id}",
    response_model=BaseResponse[ApplicationStatusResponse],
    summary="Update application status"
)
async def update_application_status(
    status_id: int,
    status_data: ApplicationStatusUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update an existing application status.
    """
    try:
        updated_status = await master_application_status_service.update_application_status(
            status_id, status_data
        )
        
        if not updated_status:
            return not_found_response()
        
        return success_response(
            data=updated_status,
        )
    except ValueError as e:
        return bad_request_response(message=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating application status {status_id}: {str(e)}")
        raise 


@router.delete(
    "/{status_id}",
    response_model=BaseResponse[dict],
    summary="Delete application status"
)
async def delete_application_status(
    status_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete an application status.
    """
    try:
        success = await master_application_status_service.delete_application_status(status_id)
        
        if not success:
            return not_found_response()
        
        return success_response(
            data={}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting application status {status_id}: {str(e)}")
        raise