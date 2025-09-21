# define your pydantic models here for request and response.
from pydantic import BaseModel,  EmailStr
from typing import List, Optional


class LogoutSuccess(BaseModel):
    inactive: bool
    token: str


class AuthToken(BaseModel):
    token: str


class ConfirmationToken(BaseModel):
    token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str



class UserCredentials(BaseModel):
    email: EmailStr
    password: str

class CreateUserObject(UserCredentials):
    pass  # Only email and password from UserCredentials


class PublicUser(BaseModel):
    id: int
    email: str
    role: str


    class Config:
        from_attributes = True


class OrganizationMembership(BaseModel):
    id: int
    user_id: int
    organization_id: int
    organization_name: str
    role: str
    is_solo: bool

    class Config:
        from_attributes = True


class UserMembershipsResponse(BaseModel):
    memberships: List[OrganizationMembership]

    class Config:
        from_attributes = True
