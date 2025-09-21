from fastapi import Header, Depends, status, Request
from fastapi.exceptions import HTTPException
from typing import Annotated, Optional
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from models.user import Token, User
from sqlalchemy.orm import Session
import os
import sys
from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime
from models.organization import OrganizationUser

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))
sys.path.append(BASE_DIR)


async def get_token_header(x_token: Annotated[str, Header()]):
    if x_token != "fake-super-secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")

# use this as middleware for requests. pass as a depenedency
# will create one for auth


async def get_query_token(token: str):
    if token != "jessica":
        raise HTTPException(
            status_code=400, detail="No Jessica token provided")


async def get_db():
    DATABASE_URL = os.environ['DATABASE_URL']
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Custom optional OAuth2 scheme that doesn't raise errors when no token is provided
class OptionalOAuth2PasswordBearer(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> Optional[str]:
        try:
            return await super().__call__(request)
        except HTTPException:
            return None

oauth2_scheme_optional = OptionalOAuth2PasswordBearer(tokenUrl="/login", auto_error=False)

# will act as the dependency when you require a user login.
# user object will always be available through this when it is required.
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Verify the token and retrieve the user
    db_token = db.query(Token).filter(Token.token == token).first()

    if not db_token:
        raise HTTPException(status_code=401, detail="Invalid token")

    if not db_token.is_active:
        raise HTTPException(status_code=401, detail="Token is inactive")

    # Check if the token is expired
    if db_token.expires_at and db_token.expires_at < datetime.utcnow():
        # Token is expired, update is_active to False and raise an exception
        db_token.is_active = False
        db.commit()
        raise HTTPException(status_code=401, detail="Token has expired")

    return db_token.user

def get_current_user_optional(token: Optional[str] = Depends(oauth2_scheme_optional), db: Session = Depends(get_db)) -> Optional[User]:
    """
    Optional user dependency - returns User if authenticated, None if not.
    Does not raise exceptions for missing/invalid tokens.
    """
    if not token:
        return None
    
    try:
        # Verify the token and retrieve the user
        db_token = db.query(Token).filter(Token.token == token).first()

        if not db_token or not db_token.is_active:
            return None

        # Check if the token is expired
        if db_token.expires_at and db_token.expires_at < datetime.utcnow():
            # Token is expired, update is_active to False
            db_token.is_active = False
            db.commit()
            return None

        return db_token.user
    except Exception:
        # If any error occurs, just return None (anonymous user)
        return None

async def require_superadmin_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to check if the current user is a superadmin or admin.
    Raises 403 if user doesn't have required role.
    """
    if current_user.role not in ["superadmin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Requires superadmin or admin role."
        )
    return current_user

async def require_superadmin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to check if the current user is a superadmin.
    Raises 403 if user doesn't have superadmin role.
    """
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Requires superadmin role."
        )
    return current_user


def require_organization_admin(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to check if the current user is an admin of a specific organization.
    Raises 403 if the user is not an admin of the organization.
    """
    from types_definitions.organization_user import OrganizationUserRole

    membership = db.query(OrganizationUser).filter(
        OrganizationUser.user_id == current_user.id,
        OrganizationUser.organization_id == org_id
    ).first()

    if not membership or membership.role != OrganizationUserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have admin privileges for this organization."
        )
    
    return current_user


async def require_organization_moderator_or_admin(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to check if the current user is a moderator or admin of a specific organization.
    Raises 403 if the user is not a moderator or admin of the organization.
    """
    from types_definitions.organization_user import OrganizationUserRole


    membership = db.query(OrganizationUser).filter(
        OrganizationUser.user_id == current_user.id,
        OrganizationUser.organization_id == org_id
    ).first()

    if not membership or membership.role not in [OrganizationUserRole.ADMIN, OrganizationUserRole.MODERATOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have sufficient privileges for this organization."
        )
    
    return current_user