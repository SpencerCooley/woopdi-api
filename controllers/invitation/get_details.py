from sqlalchemy.orm import Session
from models.invitation import Invitation
from models.user import User
from models.organization import Organization
from types_definitions.invitation import InvitationDetailsResponse
from fastapi import HTTPException, status
from datetime import datetime


def get_details(db: Session, token: str) -> InvitationDetailsResponse:
    # Find the invitation by token
    invitation = db.query(Invitation).filter(Invitation.token == token).first()
    
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found.")
    
    # Check if invitation is expired
    if datetime.utcnow() > invitation.expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation has expired.")
    
    # Get organization details
    organization = db.query(Organization).filter(Organization.id == invitation.organization_id).first()
    
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    
    # Check if a user already exists with this email
    existing_user = db.query(User).filter(User.email == invitation.email).first()

    response_status = "existing_user" if existing_user else "new_user_required"

    # Return invitation details
    return InvitationDetailsResponse(
        email=invitation.email,
        organization_name=organization.name,
        status=response_status
    )