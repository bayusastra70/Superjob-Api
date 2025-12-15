from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class RejectionReasonCreate(BaseModel):
    """Schema untuk membuat rejection reason baru"""

    reason_code: str = Field(..., description="Unique code for the rejection reason")
    reason_text: str = Field(..., description="Description of the rejection reason")
    is_custom: bool = Field(
        default=False, description="Whether this is a custom reason"
    )
    created_by: Optional[int] = Field(
        None, description="User ID who created this reason"
    )


class RejectionReasonUpdate(BaseModel):
    """Schema untuk update rejection reason"""

    reason_code: Optional[str] = None
    reason_text: Optional[str] = None
    is_active: Optional[bool] = None


class RejectionReasonResponse(BaseModel):
    """
    Schema untuk response rejection reason.

    **Test Endpoint:** GET /api/v1/rejection-reasons/

    **Test Data yang tersedia (ID 1-11):**
    - `SKILL_MISMATCH` - Keterampilan tidak sesuai
    - `EXPERIENCE_LACK` - Pengalaman kurang
    - `SALARY_MISMATCH` - Ekspektasi gaji tidak sesuai
    - `CULTURE_FIT` - Tidak cocok dengan budaya perusahaan
    - `COMMUNICATION` - Kemampuan komunikasi kurang
    - `POSITION_FILLED` - Posisi sudah terisi
    - `NO_RESPONSE` - Kandidat tidak merespons
    - `DOCUMENT_INCOMPLETE` - Dokumen tidak lengkap
    - `OVERQUALIFIED` - Terlalu berkualifikasi
    - `LOCATION_ISSUE` - Lokasi tidak sesuai
    - `OTHER` - Alasan lainnya
    """

    id: int
    reason_code: str
    reason_text: str
    is_custom: bool
    is_active: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
