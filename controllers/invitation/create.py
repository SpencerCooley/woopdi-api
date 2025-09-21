import secrets
import datetime
from sqlalchemy.orm import Session
from models.invitation import Invitation
from models.user import User
from models.organization import Organization
from types_definitions.invitation import InvitationCreate, InvitationRead
from fastapi import HTTPException, status
from services.email_service import woopdi_mail
import os


def create(db: Session, invitation: InvitationCreate, inviter: User) -> InvitationRead:

    # Verify organization exists
    organization = db.query(Organization).filter(Organization.id == invitation.organization_id).first()
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    # Create a unique token
    token = secrets.token_urlsafe(32)

    # Create the invitation
    db_invitation = Invitation(
        email=invitation.email,
        organization_id=invitation.organization_id,
        inviter_id=inviter.id,
        token=token,
        expires_at=datetime.datetime.utcnow() + datetime.timedelta(days=7)
    )

    db.add(db_invitation)
    db.commit()
    db.refresh(db_invitation)

    # Send invitation email
    try:
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
        accept_link = f"{frontend_url}/accept-invitation?token={token}"
        
        woopdi_mail.notify(
            template_name="invitation",
            recipient_email=invitation.email,
            params={
                "inviter_email": inviter.email,
                "organization_name": organization.name,
                "accept_link": accept_link
            }
        )
    except Exception as e:
        # Log the error, but don't fail the request if the email fails to send.
        # The user can still be invited manually.
        print(f"Error sending invitation email: {e}")

    return db_invitation