from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.organization import Organization
from types_definitions.organization import OrganizationUpdate
from models.user import User

def update_organization(db: Session, organization_id: int, organization_data: OrganizationUpdate, current_user: User):
    # The require_organization_admin dependency handles the authorization checks.
    # We just need to handle the business logic of updating the organization.

    # Retrieve the organization from the database
    db_org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not db_org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    # Check if the organization is a solo organization
    if db_org.is_solo:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo organizations cannot be updated")

    # Update the organization name
    db_org.name = organization_data.name
    db.commit()
    db.refresh(db_org)

    return db_org