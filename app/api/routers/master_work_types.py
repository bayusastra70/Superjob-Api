from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from app.core.security import get_current_user
from app.schemas.user import UserResponse
from app.schemas.response import BaseResponse
from app.utils.response import success_response

from app.schemas.master_work_types import (
    WorkTypeCreate,
    WorkTypeUpdate,
    WorkTypeResponse,
    WorkTypeListResponse
)
from app.services.master_work_types_service import master_work_types_service

router = APIRouter(prefix="/master/work-types", tags=["Master Work Types"])


@router.get(
    "/",
    response_model=BaseResponse[WorkTypeListResponse],
    summary="Get all work types"
)
async def get_work_types(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get list of all work types.
    """
    try:
        work_types = await master_work_types_service.get_all_work_types()
        
        return success_response(
            data=WorkTypeListResponse(
                items=work_types,
                total=len(work_types)
            ),
            message="Work types retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting work types: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve work types"
        )


@router.get(
    "/{work_type_id}",
    response_model=BaseResponse[WorkTypeResponse],
    summary="Get work type by ID"
)
async def get_work_type(
    work_type_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get specific work type by ID.
    """
    try:
        work_type = await master_work_types_service.get_work_type_by_id(work_type_id)
        
        if not work_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work type not found"
            )
        
        return success_response(
            data=work_type,
            message="Work type retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting work type {work_type_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve work type"
        )


@router.post(
    "/",
    response_model=BaseResponse[WorkTypeResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create new work type"
)
async def create_work_type(
    work_type_data: WorkTypeCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new work type.
    """
    try:
        new_work_type = await master_work_types_service.create_work_type(work_type_data)
        
        return success_response(
            data=new_work_type,
            message="Work type created successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating work type: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create work type"
        )


@router.put(
    "/{work_type_id}",
    response_model=BaseResponse[WorkTypeResponse],
    summary="Update work type"
)
async def update_work_type(
    work_type_id: int,
    work_type_data: WorkTypeUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update an existing work type.
    """
    try:
        updated_work_type = await master_work_types_service.update_work_type(
            work_type_id, work_type_data
        )
        
        if not updated_work_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work type not found"
            )
        
        return success_response(
            data=updated_work_type,
            message="Work type updated successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating work type {work_type_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update work type"
        )


@router.delete(
    "/{work_type_id}",
    response_model=BaseResponse[dict],
    summary="Delete work type"
)
async def delete_work_type(
    work_type_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete a work type.
    """
    try:
        success = await master_work_types_service.delete_work_type(work_type_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Work type not found"
            )
        
        return success_response(
            data={},
            message="Work type deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting work type {work_type_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete work type"
        )