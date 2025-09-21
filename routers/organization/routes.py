from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from dependencies.dependencies import get_db, require_superadmin_or_admin, get_current_user, require_organization_admin
from controllers.organization.list import list_organizations
from controllers.organization.update import update_organization
from controllers.organization.create_nonsolo import create_nonsolo_organization as create_user_organization
from types_definitions.organization import OrganizationRead, OrganizationUpdate
from models.user import User

router = APIRouter(prefix="/organizations", tags=["Organizations"])

@router.get("/", response_model=list[OrganizationRead])
async def list_organizations_endpoint(
    skip: int = 0,
    limit: int = 100,
    is_solo: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin_or_admin)
):
    """
    List all organizations with pagination.
    
    Accessible to superadmins and admins.
    """
    organizations = list_organizations(db, skip, limit, is_solo)
    return organizations

@router.put("/{organization_id}", response_model=OrganizationRead)
async def update_organization_endpoint(
    organization_id: int,
    organization_data: OrganizationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an organization's name.

    Accessible only to users with the ADMIN role in the organization.
    Solo organizations cannot be updated.
    """
    require_organization_admin(org_id=organization_id, current_user=current_user, db=db)
    return update_organization(db, organization_id, organization_data, current_user)


@router.post("/create-organization", response_model=OrganizationRead)
async def create_user_organization_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a non-solo organization for the current user if they don't already own one.

    Users can only own 1 non-solo organization. This endpoint allows users to create
    their own organization if they don't have one (e.g., users who were invited
    to an organization but don't have their own org yet).
    """
    return create_user_organization(db, current_user)
