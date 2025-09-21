from typing import List
from sqlalchemy.orm import Session
from models.organization import OrganizationUser, Organization
from models.user import User
from types_definitions.user import OrganizationMembership, UserMembershipsResponse


# should only include is_solo false organizations. 
def get_user_memberships(db: Session, user: User) -> List[OrganizationMembership]:
    """
    Get all organization memberships for a user.
    
    Args:
        db: Database session
        user: User object
        
    Returns:
        List of OrganizationMembership objects
    """
    # Query to get all organization memberships for the user
    user_memberships = db.query(OrganizationUser)\
        .filter(OrganizationUser.user_id == user.id)\
        .join(Organization)\
        .filter(Organization.is_solo == False)\
        .order_by(Organization.id)\
        .all()
    
    # Convert to OrganizationMembership objects
    memberships = []
    for membership in user_memberships:
        memberships.append(OrganizationMembership(
            id=membership.id,
            user_id=membership.user_id,
            organization_id=membership.organization_id,
            organization_name=membership.organization.name,
            role=membership.role.value,
            is_solo=membership.organization.is_solo
        ))
    
    return memberships
