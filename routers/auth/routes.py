# define your routes here.
from fastapi import APIRouter, Depends, HTTPException
from dependencies.dependencies import get_db
from sqlalchemy.orm import Session
from types_definitions.user import UserCredentials, AuthToken, LogoutSuccess, CreateUserObject, PublicUser, PasswordResetRequest, PasswordReset
import controllers

from typing import Annotated
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    # dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)

@router.post("/login", response_model=AuthToken)
async def login_to_retrieve_token(user: UserCredentials, db: Session = Depends(get_db)):
    """
    This endpoint will return an auth token when provided with a valid email and password. The token should be saved on the client to be used to access endpoints that require authentication.  
    """
    token = controllers.user.retrieve_token(db, user)

    if token == None:
        email = user.email
        raise HTTPException(
            status_code=401, detail=f"email or password is invalid")
    return AuthToken(**token)


@router.delete("/logout", response_model=LogoutSuccess)
async def logout(token: str, db: Session = Depends(get_db)):
    """
    This endpoint destroys the token making it invalid for future use. You will need to use /login to generate a new token.
    """
    logged_out = controllers.user.delete_token(db, token)
    if logged_out:
        return LogoutSuccess(token=token, inactive=True)
    raise HTTPException(
        status_code=409, detail=f"that token is invalid")

@router.post("/request-password-reset", status_code=200)
def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)):
    return controllers.user.request_password_reset(db, request.email)

@router.post("/reset-password", status_code=200)
def reset_password(request: PasswordReset, db: Session = Depends(get_db)):
    result = controllers.user.reset_password(db, request.token, request.new_password)
    if not result:
        raise HTTPException(status_code=400, detail="Invalid or expired token.")
    return result
