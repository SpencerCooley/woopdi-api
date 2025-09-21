from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime

class CreateLeadObject(BaseModel):
    email: EmailStr
    source: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    converted: Optional[bool] = False

class PublicLead(BaseModel):
    id: int
    email: str
    source: Optional[str]
    data: Optional[Dict[str, Any]]
    converted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LeadListResponse(BaseModel):
    leads: List[PublicLead]
    total: int
    skip: int
    limit: int

class DeleteLeadResponse(BaseModel):
    success: bool
    message: str 