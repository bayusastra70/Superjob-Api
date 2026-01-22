from fastapi import Depends, APIRouter, HTTPException, status
import httpx
import logging
from typing import Any, List


from app.schemas.response import BaseResponse
from app.utils.response import (
    success_response
)

from app.schemas.user import UserResponse
from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/locations", tags=["Locations"])

EMSIFA_BASE_URL = "https://www.emsifa.com/api-wilayah-indonesia/api"
EMSIFA_PROVINCE_URL = f"{EMSIFA_BASE_URL}/provinces.json"


# @router.get(
#     "/provinces",
#     response_model=BaseResponse[List[Any]]
# )
# async def get_indonesia_provinces(current_user: UserResponse = Depends(get_current_user)) -> BaseResponse[List[Any]]:
#     try:
#         async with httpx.AsyncClient(timeout=10) as client:
#             response = await client.get(EMSIFA_PROVINCE_URL)

#         if response.status_code != 200:
#             logger.error("EMSIFA API error: %s", response.text)
#             raise HTTPException(
#                 status_code=status.HTTP_502_BAD_GATEWAY,
#                 detail="Failed to fetch provinces from external API"
#             )


#         return success_response(
#             data=response.json(),
#             message="Indonesia provinces retrieved successfully"
#         )

#     except httpx.RequestError as e:
#         logger.exception("Request error to EMSIFA API")
#         raise


@router.get(
    "/provinces",
    response_model=BaseResponse[List[Any]]
)
async def get_indonesia_provinces(
    current_user: UserResponse = Depends(get_current_user)
) -> BaseResponse[List[Any]]:
    """
    Get all provinces in Indonesia with their regencies
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Fetch provinces
            response = await client.get(EMSIFA_PROVINCE_URL)

            if response.status_code != 200:
                logger.error("EMSIFA API error: %s", response.text)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to fetch provinces from external API"
                )

            provinces = response.json()
            
            # Buat list untuk menyimpan provinces dengan regencies
            provinces_with_regencies = []
            
            # Loop melalui semua province
            for province in provinces:
                province_id = province["id"]
                
                # Fetch regencies untuk province ini
                url = f"{EMSIFA_BASE_URL}/regencies/{province_id}.json"
                try:
                    regencies_response = await client.get(url, timeout=10)
                    
                    if regencies_response.status_code == 200:
                        regencies = regencies_response.json()
                    else:
                        regencies = []
                        logger.warning(f"Failed to fetch regencies for province {province_id}")
                except Exception as e:
                    regencies = []
                    logger.error(f"Error fetching regencies for province {province_id}: {str(e)}")
                
                # Tambahkan province dengan regencies ke list
                provinces_with_regencies.append({
                    "id": province["id"],
                    "name": province["name"],
                    "regencies": regencies
                })
            
            return success_response(
                data=provinces_with_regencies,
                message="Indonesia provinces with regencies retrieved successfully"
            )

    except httpx.RequestError as e:
        logger.exception("Request error to EMSIFA API")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="External API service unavailable"
        )


async def _get_province_with_regencies(client: httpx.AsyncClient, province: dict) -> dict:
    """
    Fetch regencies for a single province
    """
    province_id = province["id"]
    try:
        url = f"{EMSIFA_BASE_URL}/regencies/{province_id}.json"
        regencies_response = await client.get(url, timeout=10)
        
        if regencies_response.status_code == 200:
            regencies = regencies_response.json()
        else:
            regencies = []
            logger.warning(f"Failed to fetch regencies for province {province_id}")
    
    except Exception as e:
        regencies = []
        logger.error(f"Error fetching regencies for province {province_id}: {str(e)}")
    
    # Return province dengan regencies
    return {
        "id": province["id"],
        "name": province["name"],
        "regencies": regencies
    }


@router.get(
    "/provinces/{province_id}/regencies",
    response_model=BaseResponse[List[Any]]
)
async def get_regencies_by_province(
    province_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> BaseResponse[List[Any]]:
    """
    Get all regencies/kota by province ID
    Example: /api/locations/provinces/31/regencies
    """
    try:
        url = f"{EMSIFA_BASE_URL}/regencies/{province_id}.json"
        
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)

        if response.status_code != 200:
            logger.error(f"EMSIFA API error for province {province_id}: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to fetch regencies for province {province_id}"
            )

        return success_response(
            data=response.json(),
            message=f"Regencies for province {province_id} retrieved successfully"
        )

    except httpx.RequestError as e:
        logger.exception(f"Request error to EMSIFA API for province {province_id}")
        raise
