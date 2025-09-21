from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from models.user import User
from types_definitions.organization_user import OrganizationUserRead, OrganizationUserRoleUpdate
from dependencies.dependencies import get_db, get_current_user, require_organization_moderator_or_admin
import controllers.organization_user


router = APIRouter(
    prefix="/organization-users",
    tags=["Organizations"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{org_id}", response_model=List[OrganizationUserRead])
def get_users_in_organization(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_user: User = Depends(require_organization_moderator_or_admin)
):
    """
    List all users in an organization.
    Requires moderator or admin privileges for the organization.
    """
    return controllers.organization_user.list_users_in_organization(db=db, org_id=org_id)

@router.put("/{org_id}/{user_id}", response_model=OrganizationUserRead)
def update_user_role_in_organization(
    org_id: int,
    user_id: int,
    role_update: OrganizationUserRoleUpdate,
    db: Session = Depends(get_db),
    organization_user: User = Depends(require_organization_moderator_or_admin)
):
    """
    Update a user's role in an organization.
    Requires moderator or admin privileges for the organization.
    """
    try:
        updated_user = controllers.organization_user.update_user_role(
            db=db, 
            org_id=org_id, 
            user_id=user_id, 
            new_role=role_update.role, 
            current_user=organization_user
        )
        return updated_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{org_id}/{user_id}")
def remove_user_from_organization_endpoint(
    org_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    organization_user: User = Depends(require_organization_moderator_or_admin)
):
    """
    Remove a user from an organization.
    Requires moderator or admin privileges for the organization.
    """
    try:
        controllers.organization_user.remove_user_from_organization(db=db, org_id=org_id, user_id=user_id, current_user=organization_user)
        return {"message": "User removed from organization successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))