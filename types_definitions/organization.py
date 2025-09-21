from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class OrganizationBase(BaseModel):
    name: str
    description: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: str

class OrganizationResponse(OrganizationBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class OrganizationRead(OrganizationBase):
    id: int
    created_at: datetime
    updated_at: datetime
    is_solo: bool
    org_owner: int

    model_config = ConfigDict(from_attributes=True)
