from models.user import User, Token
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
import jwt
import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from fastapi import HTTPException

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))
JWT_SECRET = os.environ['JWT_SECRET']


def retrieve_token(db, user):
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    db_user = db.query(User).filter(User.email == user.email).first()
    # first check if user exists
    if not db_user:
        #need to return a better error message  
        raise HTTPException(status_code=401, detail="Invalid email or password")

    password_valid = pwd_context.verify(user.password, db_user.hashed_password)

    if db_user and password_valid:
        # Create a JWT token with a 168-hour expiration period
        expiration_time = datetime.utcnow() + timedelta(hours=168)
        payload = {
            "sub": str(db_user.id),
            "exp": expiration_time,
            # You can include additional information in the payload if needed
            # For example, user roles, permissions, etc.
        }

        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

        # Associate the token with the user
        new_token = Token(
            token=token, expires_at=expiration_time, user=db_user)
        db.add(new_token)
        db.commit()

        return {"token": token}

    return None
