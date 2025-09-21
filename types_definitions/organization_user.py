from pydantic import BaseModel
from typing import Optional
from enum import Enum

class OrganizationUserRole(str, Enum):
    ADMIN = "ADMIN"
    MODERATOR = "MODERATOR"
    MEMBER = "MEMBER"

class OrganizationUserRead(BaseModel):
    id: int
    user_id: int
    organization_id: int
    role: OrganizationUserRole
    user_email: str
    user_confirmed: bool
    user_role: str
    
    class Config:
        orm_mode = True

class OrganizationUserRoleUpdate(BaseModel):
    role: OrganizationUserRole