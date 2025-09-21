from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import Union
from models.user import User
from types_definitions.invitation import InvitationCreate, InvitationRead, InvitationDetailsResponse, InvitationAccept, SuccessResponse
from types_definitions.user import AuthToken
from dependencies.dependencies import get_db, get_current_user, require_organization_moderator_or_admin
import controllers.invitation

router = APIRouter(
    prefix="/invitations",
    tags=["Users"],
    responses={404: {"description": "Not found"}},
)

@router.post("", response_model=InvitationRead, status_code=status.HTTP_201_CREATED)
async def invite_user(
    invitation: InvitationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Invite a user to an organization.
    """
    # Check if the current user is an admin of the organization
    await require_organization_moderator_or_admin(org_id=invitation.organization_id, current_user=current_user, db=db)
    
    return controllers.invitation.create(db=db, invitation=invitation, inviter=current_user)

@router.get("/details", response_model=InvitationDetailsResponse)
def get_invitation_details(token: str, db: Session = Depends(get_db)):
    """
    Get the details of an invitation to determine the next step in the acceptance process.
    """
    return controllers.invitation.get_details(db=db, token=token)

@router.post("/accept", response_model=Union[AuthToken, SuccessResponse])
def accept_invitation(
    acceptance_data: InvitationAccept,
    db: Session = Depends(get_db)
):
    """
    Accept an invitation. This will either create a new user and return an auth token,
    or add an existing user to the new organization.
    """
    return controllers.invitation.accept(db=db, invitation_accept_data=acceptance_data)