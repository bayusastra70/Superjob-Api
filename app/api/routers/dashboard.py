from fastapi import APIRouter, HTTPException, Depends, Query, Path, Request
from typing import Optional
from loguru import logger

from app.schemas.response import BaseResponse
from app.schemas.dashboard import DashboardDataResponse
from app.services.dashboard_service import dashboard_service
from app.utils.response import success_response, not_found_response
from app.schemas.user import UserResponse
from app.core.security import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/",
    response_model=BaseResponse[DashboardDataResponse],
    summary="Get Dashboard Data",
    
)
async def get_dashboard(
    current_user: UserResponse = Depends(get_current_user),
) -> BaseResponse[DashboardDataResponse]:
    """Get employer dashboard data"""
    try:
        # Get dashboard data from service
        dashboard_data = dashboard_service.get_dashboard_data(current_user)
        
        return success_response(
            data=dashboard_data,
        )
        
    except Exception as e:
        logger.error(f"Dashboard endpoint error: {e}")
        raise