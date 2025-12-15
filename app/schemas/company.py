from typing import Optional

from pydantic import BaseModel


class CompanyProfileOut(BaseModel):
    employer_id: int
    name: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
