from sqlalchemy.orm import Session
from models import User, ResetPasswordRequest
from utils.password import get_password_hash
from services.email_service import woopdi_mail
import datetime

def reset_password(db: Session, token: str, new_password: str):
    # Find the token in the database
    reset_password_request = db.query(ResetPasswordRequest).filter(ResetPasswordRequest.token == token).first()

    # Check if the token is valid
    if not reset_password_request or not reset_password_request.valid or reset_password_request.used or reset_password_request.expires_at < datetime.datetime.utcnow():
        return None

    # Get the user
    user = db.query(User).filter(User.id == reset_password_request.user_id).first()
    if not user:
        return None

    # Hash the new password and update the user's password
    user.hashed_password = get_password_hash(new_password)

    # Mark the token as used
    reset_password_request.used = True

    db.commit()

    # Send a confirmation email
    woopdi_mail.notify(
        template_name="password_reset_success",
        recipient_email=user.email,
        params={"email": user.email}
    )

    return {"message": "Password has been reset successfully."}
