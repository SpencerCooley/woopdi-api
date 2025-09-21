from sqlalchemy.orm import Session
from models.organization import OrganizationUser
from models.user import User
from fastapi import HTTPException, status
from types_definitions.organization_user import OrganizationUserRole

def remove_user_from_organization(db: Session, org_id: int, user_id: int, current_user: User) -> dict:
    """Remove a user from an organization."""
    
    # Verify the user being deleted is a member of the organization
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
        raise HTTPException(status_code=403, detail="Members cannot delete users from organization")
    
    # MODERATOR permissions: can only delete MEMBER users
    if requester_membership.role == OrganizationUserRole.MODERATOR:
        # Moderators can only delete MEMBER users
        if membership.role != OrganizationUserRole.MEMBER:
            raise HTTPException(
                status_code=403, 
                detail="Moderators can only delete users with MEMBER role"
            )
    
    # ADMIN permissions: can delete anyone
    elif requester_membership.role == OrganizationUserRole.ADMIN:
        # Admins have full permissions - no additional checks needed
        pass
    
    else:
        # This shouldn't happen, but safety check
        raise HTTPException(status_code=403, detail="Invalid role for this operation")
    
    # Prevent users from deleting themselves (optional business rule)
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="You cannot delete yourself from the organization")
    
    # Delete the membership
    db.delete(membership)
    db.commit()
    
    return {"message": f"User successfully removed from organization", "deleted_user_id": user_id}
