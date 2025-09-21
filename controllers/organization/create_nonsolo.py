from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.organization import Organization, OrganizationUser
from models.user import User
from types_definitions.organization_user import OrganizationUserRole
import stripe
from dotenv import load_dotenv
import os
import uuid

# Global variable to store stripe api key
_stripe_api_key = None

def _get_stripe_api_key():
    """Get Stripe API key, loading it if not already loaded"""
    global _stripe_api_key
    if _stripe_api_key is None:
        load_dotenv()
        _stripe_api_key = os.getenv("STRIPE_SECRET_KEY")
    return _stripe_api_key

def create_nonsolo_organization(db: Session, current_user: User):
    """
    Create a non-solo organization for a user if they don't already own one.
    Users can only own 1 non-solo organization.
    """
    # Check if user already owns a non-solo organization
    existing_non_solo_org = db.query(Organization).filter(
        Organization.org_owner == current_user.id,
        Organization.is_solo == False
    ).first()

    if existing_non_solo_org:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already own a non-solo organization."
        )

    # Initialize Stripe with API key if not already done
    stripe.api_key = _get_stripe_api_key()

    # Create the Stripe Customer for non-solo organization
    try:
        non_solo_stripe_customer = stripe.Customer.create(
            email=current_user.email,
            name=f"{current_user.email} - TEAM",
            metadata={"role": current_user.role, "org_type": "team"}
        )
    except stripe.error.StripeError as e:
        if "email" in str(e).lower() and "already exists" in str(e).lower():
            # If customer with this email already exists, create with a unique email
            unique_suffix = str(uuid.uuid4())[:8]
            unique_email = f"{current_user.email.split('@')[0]}+team+{unique_suffix}@{current_user.email.split('@')[1]}"
            non_solo_stripe_customer = stripe.Customer.create(
                email=unique_email,
                name=f"{current_user.email} - TEAM",
                metadata={"role": current_user.role, "org_type": "team", "original_email": current_user.email}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stripe error: {str(e)}"
            )

    # Create the non-solo Organization for the user
    db_non_solo_organization = Organization(
        name=f"{current_user.email}'s Team",
        is_solo=False,
        org_owner=current_user.id,
        stripe_customer_id=non_solo_stripe_customer.id
    )
    db.add(db_non_solo_organization)
    db.flush()

    # Link the user to the organization with an ADMIN role
    db_non_solo_org_user_link = OrganizationUser(
        user_id=current_user.id,
        organization_id=db_non_solo_organization.id,
        role=OrganizationUserRole.ADMIN
    )
    db.add(db_non_solo_org_user_link)

    # Commit the transaction
    db.commit()
    db.refresh(db_non_solo_organization)

    return db_non_solo_organization
