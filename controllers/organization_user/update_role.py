from sqlalchemy.orm import Session
from models.organization import OrganizationUser
from models.user import User
from typing import List
from fastapi import HTTPException, status
from types_definitions.organization_user import OrganizationUserRead, OrganizationUserRole

def update_user_role(db: Session, org_id: int, user_id: int, new_role: OrganizationUserRole, current_user: User) -> OrganizationUserRead:
    """Update a user's role in an organization."""
    
    # Verify the user being modified is a member of the organization
    membership = db.query(OrganizationUser).filter(
        OrganizationUser.organization_id == org_id,
        OrganizationUser.user_id == user_id
    ).first()
    
    if not membership:
        raise HTTPException(status_code=404, detail="The user cannot be found in organization")
    
    # Get the membership of the user making the request
    requester_membership = db.query(OrganizationUser).filter(
        OrganizationUser.user_id == current_user.id,
        OrganizationUser.organization_id == org_id
    ).first()
    
    if not requester_membership:
        raise HTTPException(status_code=403, detail="You are not a member of this organization")
    
    # MEMBER users should never reach this function (handled by dependency)
    # But let's add a safety check
    if requester_membership.role == OrganizationUserRole.MEMBER:
        raise HTTPException(status_code=403, detail="Members cannot modify user roles")
    
    # MODERATOR permissions: can only change MEMBER users to MODERATOR
    if requester_membership.role == OrganizationUserRole.MODERATOR:
        # Moderators can only modify MEMBER users
        if membership.role != OrganizationUserRole.MEMBER:
            raise HTTPException(
                status_code=403, 
                detail="Moderators can only modify users with MEMBER role"
            )
        
        # Moderators can only promote to MODERATOR role
        if new_role != OrganizationUserRole.MODERATOR:
            raise HTTPException(
                status_code=403, 
                detail="Moderators can only promote members to MODERATOR role"
            )
    
    # ADMIN permissions: can change anyone to any role
    elif requester_membership.role == OrganizationUserRole.ADMIN:
        # Admins have full permissions - no additional checks needed
        pass
    
    else:
        # This shouldn't happen, but safety check
        raise HTTPException(status_code=403, detail="Invalid role for this operation")
    
    # Prevent users from modifying their own role (optional business rule)
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot modify your own role")
    
    # Update the role
    membership.role = new_role
    db.commit()
    db.refresh(membership)
    
    # Return enriched user information to match the response model
    enriched_user = OrganizationUserRead(
        id=membership.id,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        role=membership.role,
        user_email=membership.user.email,
        user_confirmed=membership.user.confirmed,
        user_role=membership.user.role.value
    )
    
    return enriched_user