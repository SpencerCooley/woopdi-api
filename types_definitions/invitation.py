# define your pydantic models here for request and response.
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime


class InvitationCreate(BaseModel):
    email: EmailStr
    organization_id: int


class InvitationRead(BaseModel):
    email: EmailStr
    id: int
    organization_id: int
    inviter_id: int
    status: str
    expires_at: datetime

    class Config:
        from_attributes = True


class InvitationDetailsResponse(BaseModel):
    status: str
    email: EmailStr
    organization_name: str

    class Config:
        from_attributes = True


class InvitationAccept(BaseModel):
    token: str
    password: Optional[str] = None

    class Config:
        from_attributes = True


class SuccessResponse(BaseModel):
    message: str

    class Config:
        from_attributes = True