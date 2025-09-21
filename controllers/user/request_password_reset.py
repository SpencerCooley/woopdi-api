
from sqlalchemy.orm import Session
from models import User, ResetPasswordRequest
from utils.token import generate_secure_token
from services.email_service import woopdi_mail
from fastapi import HTTPException
import os
from dotenv import load_dotenv

load_dotenv()

def request_password_reset(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Note: For security, we don't reveal if the user exists or not.
        # We'll just return a success response to prevent user enumeration.
        return {"message": "If an account with this email exists, a password reset link has been sent."}

    # Invalidate all previous reset tokens for this user
    db.query(ResetPasswordRequest).filter(ResetPasswordRequest.user_id == user.id).update({"valid": False})

    # Create a new reset token
    reset_token = generate_secure_token()
    db_token = ResetPasswordRequest(user_id=user.id, token=reset_token)
    db.add(db_token)
    db.commit()

    # Send the password reset email
    client_url = os.getenv("WEB_CLIENT_URL", "http://localhost:3000")
    reset_url = f"{client_url}/reset-password?token={reset_token}"

    try:
        woopdi_mail.notify(
            template_name='reset_password',
            recipient_email=user.email,
            params={'reset_url': reset_url}
        )
    except Exception as e:
        # Even if the email fails, we don't want to reveal this to the user.
        # Log the error for debugging.
        print(f"Error sending password reset email: {e}")
        # Potentially add more robust logging here
        pass

    return {"message": "If an account with this email exists, a password reset link has been sent."}