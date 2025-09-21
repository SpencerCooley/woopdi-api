from sqlalchemy.orm import Session
from models.organization import OrganizationUser
from models.user import User
from typing import List
from types_definitions.organization_user import OrganizationUserRead

def list_users_in_organization(db: Session, org_id: int) -> List[OrganizationUserRead]:
    """List all users in an organization with enriched user information."""
    # Query organization users with joined user information
    organization_users = db.query(OrganizationUser)\
        .join(User, OrganizationUser.user_id == User.id)\
        .filter(OrganizationUser.organization_id == org_id)\
        .all()
    
    # Convert to the enriched schema
    enriched_users = []
    for org_user in organization_users:
        enriched_user = OrganizationUserRead(
            id=org_user.id,
            user_id=org_user.user_id,
            organization_id=org_user.organization_id,
            role=org_user.role,
            user_email=org_user.user.email,
            user_confirmed=org_user.user.confirmed,
            user_role=org_user.user.role.value
        )
        enriched_users.append(enriched_user)
    
    return enriched_users