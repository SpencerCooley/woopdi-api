from fastapi import APIRouter, Depends, HTTPException
from types_definitions.user import (
    PublicUser,
    CreateUserObject,
    AuthToken,
    ConfirmationToken,
    UserMembershipsResponse
)
from types_definitions.subscription import SubscriptionStatusResponse, PublicSubscription
from dependencies.dependencies import get_current_user, get_db, require_superadmin_or_admin
from sqlalchemy.orm import Session
from models.user import User
import controllers

router = APIRouter(
    prefix="/user",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=PublicUser)
async def create_new_user(user: CreateUserObject, db: Session = Depends(get_db)):
    """Create a new user (public endpoint)"""
    db_user = controllers.user.create(db, user)
    if db_user is None:
        email = user.email
        raise HTTPException(
            status_code=409, detail=f"A user with email {email} already exists")
    
    return PublicUser(
        id=db_user.id,
        email=db_user.email,
        role=db_user.role.value
    )

@router.post("/admin", response_model=PublicUser)
async def create_admin_user(
    user: CreateUserObject, 
    db: Session = Depends(get_db),
    current_user: PublicUser = Depends(require_superadmin_or_admin)
):
    """Create a new admin user (requires superadmin permissions)"""
    db_user = controllers.user.create(db, user, role="admin")
    if db_user is None:
        email = user.email
        raise HTTPException(
            status_code=409, detail=f"A user with email {email} already exists")
    
    return PublicUser(
        id=db_user.id,
        email=db_user.email,
        role=db_user.role.value
    )

@router.get("/me", response_model=PublicUser)
async def get_current_user(current_user: PublicUser = Depends(get_current_user)):
    return current_user


@router.get("/memberships", response_model=UserMembershipsResponse)
async def get_user_memberships(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all organization memberships for the current user."""
    memberships = controllers.user.get_user_memberships(db, current_user)
    return UserMembershipsResponse(memberships=memberships)


@router.get("/confirm", response_model=AuthToken)
async def confirm_user_by_email(token: str, db: Session = Depends(get_db)):
    """Confirm user's email with a token and return an auth token."""
    confirmed_user_token = controllers.user.confirm_signup(db, token)
    return AuthToken(**confirmed_user_token)

@router.post("/resend-confirmation", status_code=202)
async def resend_confirmation_email(token: str, db: Session = Depends(get_db)):
    """Resend confirmation email with a new token."""
    controllers.user.resend_confirmation(db, token)
    return {"message": "If the user exists and is not confirmed, a new confirmation email has been sent."}


# New system-wide user listing endpoint
@router.get("/list", response_model=list[PublicUser])
async def list_users_endpoint(
    skip: int = 0,
    limit: int = 100,
    role: str = None,
    confirmed: bool = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_superadmin_or_admin)
):
    """
    List all users with pagination.
    
    Accessible to superadmins and admins.
    """
    users = controllers.user.list_users(db, skip, limit, role, confirmed)
    return users
