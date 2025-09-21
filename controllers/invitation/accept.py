from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.invitation import Invitation
from models.user import User, Token
from models.organization import OrganizationUser, Organization
from types_definitions.invitation import InvitationAccept, SuccessResponse
from types_definitions.organization_user import OrganizationUserRole
from utils.password import get_password_hash
from datetime import datetime, timedelta
import jwt
import os
import stripe
from dotenv import load_dotenv

JWT_SECRET = os.environ.get('JWT_SECRET')

# Global variable to store stripe api key
_stripe_api_key = None

def _get_stripe_api_key():
    """Get Stripe API key, loading it if not already loaded"""
    global _stripe_api_key
    if _stripe_api_key is None:
        load_dotenv()
        _stripe_api_key = os.getenv("STRIPE_SECRET_KEY")
    return _stripe_api_key

def accept(db: Session, invitation_accept_data: InvitationAccept):
    # 1. Validate the invitation token
    invitation = db.query(Invitation).filter(Invitation.token == invitation_accept_data.token).first()
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found.")
    if invitation.status != 'pending':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invitation has already been {invitation.status}.")
    if datetime.utcnow() > invitation.expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation has expired.")

    # 2. Handle the two flows: new user vs. existing user
    existing_user = db.query(User).filter(User.email == invitation.email).first()

    # --- New User Flow ---
    if invitation_accept_data.password:
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists.")

        hashed_password = get_password_hash(invitation_accept_data.password)
        new_user = User(
            email=invitation.email,
            hashed_password=hashed_password,
            confirmed=True, # Invitation acts as confirmation
            role='user' # Default role
        )
        db.add(new_user)
        db.flush() # Flush to get the new_user.id

        # Initialize Stripe with API key if not already done
        stripe.api_key = _get_stripe_api_key()

        # Create the Stripe Customer for solo organization
        try:
            solo_stripe_customer = stripe.Customer.create(
                email=new_user.email,
                name=f"{new_user.email} - SOLO",
                metadata={"role": new_user.role, "org_type": "solo"}
            )
        except stripe.error.StripeError as e:
            if "email" in str(e).lower() and "already exists" in str(e).lower():
                # If customer with this email already exists, create with a unique email
                import uuid
                unique_suffix = str(uuid.uuid4())[:8]
                unique_email = f"{new_user.email.split('@')[0]}+solo+{unique_suffix}@{new_user.email.split('@')[1]}"
                solo_stripe_customer = stripe.Customer.create(
                    email=unique_email,
                    name=f"{new_user.email} - SOLO",
                    metadata={"role": new_user.role, "org_type": "solo", "original_email": new_user.email}
                )
            else:
                raise e

        # Create the solo Organization for the user
        db_solo_organization = Organization(
            name=f"{new_user.email}'s SOLO Team",
            is_solo=True,
            org_owner=new_user.id,
            stripe_customer_id=solo_stripe_customer.id
        )
        db.add(db_solo_organization)
        db.flush()

        # Link the user to the solo organization with an ADMIN role
        db_solo_org_user_link = OrganizationUser(
            user_id=new_user.id,
            organization_id=db_solo_organization.id,
            role=OrganizationUserRole.ADMIN
        )
        db.add(db_solo_org_user_link)

        # Add user to the invited organization
        new_org_membership = OrganizationUser(
            user_id=new_user.id,
            organization_id=invitation.organization_id,
            role='MEMBER' # Default role for invitees
        )
        db.add(new_org_membership)

        invitation.status = 'accepted'

        # Create JWT and save the token
        expiration_time = datetime.utcnow() + timedelta(hours=168)
        payload = {"sub": str(new_user.id), "exp": expiration_time}
        jwt_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

        new_token_record = Token(token=jwt_token, expires_at=expiration_time, user=new_user)
        db.add(new_token_record)

        db.commit()

        return {"token": jwt_token}

    # --- Existing User Flow ---
    else:
        if not existing_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found. A password is required to create a new account.")

        # Check if user already has a solo organization
        existing_solo_org = db.query(Organization).join(OrganizationUser).filter(
            OrganizationUser.user_id == existing_user.id,
            Organization.is_solo == True
        ).first()

        # If user doesn't have a solo organization, create one
        if not existing_solo_org:
            # Initialize Stripe with API key if not already done
            stripe.api_key = _get_stripe_api_key()

            # Create the Stripe Customer for solo organization
            try:
                solo_stripe_customer = stripe.Customer.create(
                    email=existing_user.email,
                    name=f"{existing_user.email} - SOLO",
                    metadata={"role": existing_user.role, "org_type": "solo"}
                )
            except stripe.error.StripeError as e:
                if "email" in str(e).lower() and "already exists" in str(e).lower():
                    # If customer with this email already exists, create with a unique email
                    import uuid
                    unique_suffix = str(uuid.uuid4())[:8]
                    unique_email = f"{existing_user.email.split('@')[0]}+solo+{unique_suffix}@{existing_user.email.split('@')[1]}"
                    solo_stripe_customer = stripe.Customer.create(
                        email=unique_email,
                        name=f"{existing_user.email} - SOLO",
                        metadata={"role": existing_user.role, "org_type": "solo", "original_email": existing_user.email}
                    )
                else:
                    raise e

            # Create the solo Organization for the user
            db_solo_organization = Organization(
                name=f"{existing_user.email}'s SOLO Team",
                is_solo=True,
                org_owner=existing_user.id,
                stripe_customer_id=solo_stripe_customer.id
            )
            db.add(db_solo_organization)
            db.flush()

            # Link the user to the organization with an ADMIN role
            db_solo_org_user_link = OrganizationUser(
                user_id=existing_user.id,
                organization_id=db_solo_organization.id,
                role=OrganizationUserRole.ADMIN
            )
            db.add(db_solo_org_user_link)

        # Add user to the invited organization
        new_org_membership = OrganizationUser(
            user_id=existing_user.id,
            organization_id=invitation.organization_id,
            role='MEMBER' # Default role for invitees
        )
        db.add(new_org_membership)

        invitation.status = 'accepted'
        db.commit()

        return {"message": "Invitation accepted successfully. You can now access the new organization."}
