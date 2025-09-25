from sqlalchemy.orm import Session
from models.user import User
from models.organization import Organization, OrganizationUser, Subscription
from fastapi import HTTPException
from config.system_settings import SystemSettings
import uuid
import stripe
import os
from dotenv import load_dotenv
from types_definitions.organization_user import OrganizationUserRole

# Global variable to store stripe api key
_stripe_api_key = None

def _get_stripe_api_key():
    """Get Stripe API key, loading it if not already loaded"""
    global _stripe_api_key
    if _stripe_api_key is None:
        load_dotenv()
        _stripe_api_key = os.getenv("STRIPE_SECRET_KEY")
    return _stripe_api_key

def create_free_subscription(db: Session, current_user: User):
    """
    Creates a free subscription for a user if the system is configured to auto-create free subscriptions.
    """
    # Check if auto-creation of free subscriptions is enabled
    if not SystemSettings.AUTO_CREATE_FREE_SUBSCRIPTION:
        raise HTTPException(status_code=400, detail="Free subscriptions are not enabled for this system.")
    
    # Check if user already has a subscription
    existing_subscription = db.query(Subscription).join(Organization).join(OrganizationUser).filter(
        OrganizationUser.user_id == current_user.id
    ).first()
    
    if existing_subscription:
        raise HTTPException(status_code=409, detail="User already has a subscription.")
    
    # Initialize Stripe with API key
    stripe_api_key = _get_stripe_api_key()
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Stripe API key not configured")

    stripe.api_key = stripe_api_key

    # Create the Stripe Customer for non-solo organization
    try:
        non_solo_stripe_customer = stripe.Customer.create(
            email=current_user.email,
            name=f"{current_user.email} - TEAM",
            metadata={"role": "user", "org_type": "team"}
        )
    except stripe.error.StripeError as e:
        if "email" in str(e).lower() and "already exists" in str(e).lower():
            # If customer with this email already exists, create with a unique email
            unique_suffix = str(uuid.uuid4())[:8]
            unique_email = f"{current_user.email.split('@')[0]}+team+{unique_suffix}@{current_user.email.split('@')[1]}"
            non_solo_stripe_customer = stripe.Customer.create(
                email=unique_email,
                name=f"{current_user.email} - TEAM",
                metadata={"role": "user", "org_type": "team", "original_email": current_user.email}
            )
        else:
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error creating Stripe customer: {str(e)}")

    # Create a new non-solo organization for the user
    try:
        new_org = Organization(
            name=f"{current_user.email}'s Team",
            is_solo=False,
            org_owner=current_user.id,
            stripe_customer_id=non_solo_stripe_customer.id
        )
        db.add(new_org)
        db.flush()  # Flush to get the new_org.id for metadata

        # Associate the current user as an ADMIN of the new organization
        org_user_link = OrganizationUser(
            user_id=current_user.id,
            organization_id=new_org.id,
            role=OrganizationUserRole.ADMIN
        )
        db.add(org_user_link)

        # Create a free subscription record in our database
        # For a free subscription, we'll use a unique Stripe ID to avoid constraint violations
        stripe_subscription_id = f"free_subscription_{uuid.uuid4().hex[:12]}"
        db_subscription = Subscription(
            organization_id=new_org.id,
            stripe_subscription_id=stripe_subscription_id,
            status="active",
            price_id="free_plan"
        )
        db.add(db_subscription)
        db.commit()
        db.refresh(db_subscription)

        return db_subscription
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error creating organization: {str(e)}")
