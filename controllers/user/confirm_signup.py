from sqlalchemy.orm import Session
from models.user import User, EmailConfirmation, Token
from datetime import datetime, timedelta
from typing import Optional
import jwt
import os
from dotenv import load_dotenv
from fastapi import HTTPException

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))
JWT_SECRET = os.environ['JWT_SECRET']

def confirm_signup(db: Session, token: str) -> dict:
    """
    Confirms a user's email address, marks them as confirmed,
    and returns a login token.

    Args:
        db: The database session.
        token: The confirmation token sent to the user's email.

    Returns:
        A dictionary containing the auth token if successful.
        Raises HTTPException for various error conditions.
    """
    confirmation = db.query(EmailConfirmation).filter(EmailConfirmation.token == token).first()
    if not confirmation or not confirmation.valid:
        raise HTTPException(status_code=404, detail="Confirmation token not found or is invalid.")

    if confirmation.used:
        raise HTTPException(status_code=409, detail="This email address has already been confirmed. Please log in.")

    if datetime.utcnow() > confirmation.expires_at:
        raise HTTPException(status_code=410, detail="Confirmation token has expired. Please request a new one.")

    # Mark the token as used
    confirmation.used = True

    # Find the user and mark as confirmed
    user = db.query(User).filter(User.id == confirmation.user_id).first()
    if not user:
        # This case should ideally not happen if data integrity is maintained
        raise HTTPException(status_code=500, detail="Associated user not found.")
    
    user.confirmed = True
    
    # --- Create and issue a JWT token ---
    expiration_time = datetime.utcnow() + timedelta(hours=168)
    payload = {
        "sub": str(user.id),
        "exp": expiration_time,
    }
    jwt_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    # Associate the token with the user
    new_token = Token(
        token=jwt_token, expires_at=expiration_time, user=user)
    db.add(new_token)
    
    db.commit()
    db.refresh(user)
    
    return {"token": jwt_token} 


