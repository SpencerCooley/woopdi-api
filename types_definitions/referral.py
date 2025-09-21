from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class CreateReferralRequest(BaseModel):
    email: EmailStr
    campaign_reference: Optional[str] = None

class PublicReferral(BaseModel):
    """Public referral model that only exposes fields safe for users to see"""
    id: int
    referrer_id: int
    email: str
    converted: bool
    invite_sent: bool
    created_at: datetime
    campaign_reference: Optional[str]

    class Config:
        from_attributes = True

class InternalReferral(BaseModel):
    """Internal referral model with all fields - for admin/server use only"""
    id: int
    referrer_id: int
    email: str
    converted: bool
    invite_sent: bool
    created_at: datetime
    converted_at: Optional[datetime]
    referred_user_id: Optional[int]
    campaign_reference: Optional[str]

    class Config:
        from_attributes = True

class ReferralListResponse(BaseModel):
    referrals: List[PublicReferral]
    total: int
    skip: int
    limit: int 