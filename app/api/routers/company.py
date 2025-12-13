from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/company", tags=["Company"])

# Model untuk request POST
class CompanySummaryRequest(BaseModel):
    companyId: int
    month: str
    summary: str
    status: str

# Model untuk response POST
class CompanySummaryResponse(BaseModel):
    companyId: int
    month: str
    summary: str
    status: str

@router.get("/stats")
async def get_company_stats():
    """
    GET endpoint untuk mendapatkan statistik company
    """
    return {
        "totalEmployees": 150,
        "activeProjects": 8,
        "monthlyRevenue": 320000000
    }

@router.post("/summary", response_model=CompanySummaryResponse)
async def create_company_summary(request: CompanySummaryRequest):
    """
    POST endpoint untuk membuat summary company
    """
    return CompanySummaryResponse(
        companyId=request.companyId,
        month=request.month,
        summary=request.summary,
        status=request.status
    )

