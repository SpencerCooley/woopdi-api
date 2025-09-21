from sqlalchemy.orm import Session
from models.user import User, EmailConfirmation
from services.email_service import woopdi_mail
from fastapi import HTTPException
from datetime import datetime, timedelta
import secrets
import os

def resend_confirmation(db: Session, old_token: str):
    """
    Resends a confirmation email with a new token.

    Args:
        db: The database session.
        old_token: The original, possibly expired, confirmation token.
    """
    # Find the original confirmation record
    old_confirmation = db.query(EmailConfirmation).filter(EmailConfirmation.token == old_token).first()

    # If the token doesn't exist or the user is already confirmed, do nothing.
    if not old_confirmation or old_confirmation.user.confirmed:
        return

    # Invalidate the old token
    old_confirmation.valid = False

    # Create a new confirmation record
    new_token_str = secrets.token_urlsafe(32)
    new_confirmation = EmailConfirmation(
        user_id=old_confirmation.user.id,
        token=new_token_str,
        expires_at=datetime.utcnow() + timedelta(hours=2)
    )
    db.add(new_confirmation)
    
    # Commit the changes to the database
    db.commit()

    # Send the new confirmation email
    client_url = os.getenv("WEB_CLIENT_URL", "http://localhost:3000")
    confirmation_url = f"{client_url}/confirm-email?token={new_token_str}"
    woopdi_mail.notify(
        template_name="signup_confirmation",
        recipient_email=old_confirmation.user.email,
        params={
            "confirmation_url": confirmation_url,
            "email": old_confirmation.user.email
        }
    )