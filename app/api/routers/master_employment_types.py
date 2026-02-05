from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from loguru import logger

from app.core.security import get_current_user
from app.schemas.user import UserResponse
from app.schemas.response import BaseResponse
from app.utils.response import success_response

from app.schemas.master_employment_types import (
    EmploymentTypeCreate,
    EmploymentTypeUpdate,
    EmploymentTypeResponse,
    EmploymentTypeListResponse
)
from app.services.master_employment_types_service import master_employment_types_service

router = APIRouter(prefix="/master/employment-types", tags=["Master Employment Types"])


@router.get(
    "/",
    response_model=BaseResponse[EmploymentTypeListResponse],
    summary="Get all employment types"
)
async def get_employment_types(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get list of all employment types.
    """
    try:
        employment_types = await master_employment_types_service.get_all_employment_types()
        
        return success_response(
            data=EmploymentTypeListResponse(
                items=employment_types,
                total=len(employment_types)
            )
        )
    except Exception as e:
        logger.error(f"Error getting employment types: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve employment types"
        )


@router.get(
    "/select-options",
    response_model=BaseResponse[List[Dict[str, Any]]],
    summary="Get employment types for select options"
)
async def get_employment_types_select_options(
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get simplified employment types for dropdown/select components.
    Returns: [{id, name, code}]
    """
    try:
        options = await master_employment_types_service.get_employment_types_for_select()
        
        return success_response(
            data=options,
            message="Employment types options retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting employment types options: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve employment types options"
        )


@router.get(
    "/{employment_type_id}",
    response_model=BaseResponse[EmploymentTypeResponse],
    summary="Get employment type by ID"
)
async def get_employment_type(
    employment_type_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Get specific employment type by ID.
    """
    try:
        employment_type = await master_employment_types_service.get_employment_type_by_id(employment_type_id)
        
        if not employment_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employment type not found"
            )
        
        return success_response(
            data=employment_type,
            message="Employment type retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting employment type {employment_type_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve employment type"
        )


@router.post(
    "/",
    response_model=BaseResponse[EmploymentTypeResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create new employment type"
)
async def create_employment_type(
    employment_type_data: EmploymentTypeCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new employment type.
    """
    try:
        new_employment_type = await master_employment_types_service.create_employment_type(employment_type_data)
        
        if not new_employment_type:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create employment type"
            )
        
        return success_response(
            data=new_employment_type,
            message="Employment type created successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating employment type: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create employment type"
        )


@router.put(
    "/{employment_type_id}",
    response_model=BaseResponse[EmploymentTypeResponse],
    summary="Update employment type"
)
async def update_employment_type(
    employment_type_id: int,
    employment_type_data: EmploymentTypeUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update an existing employment type.
    """
    try:
        updated_employment_type = await master_employment_types_service.update_employment_type(
            employment_type_id, employment_type_data
        )
        
        if not updated_employment_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employment type not found"
            )
        
        return success_response(
            data=updated_employment_type,
            message="Employment type updated successfully"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating employment type {employment_type_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update employment type"
        )


@router.delete(
    "/{employment_type_id}",
    response_model=BaseResponse[dict],
    summary="Delete employment type"
)
async def delete_employment_type(
    employment_type_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete an employment type.
    """
    try:
        success = await master_employment_types_service.delete_employment_type(employment_type_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employment type not found"
            )
        
        return success_response(
            data={},
            message="Employment type deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting employment type {employment_type_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete employment type"
        )