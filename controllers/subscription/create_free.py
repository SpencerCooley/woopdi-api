from sqlalchemy.orm import Session
from models.user import User
from models.organization import Organization, OrganizationUser, Subscription
from fastapi import HTTPException
from config.system_settings import SystemSettings
import uuid
from types_definitions.organization_user import OrganizationUserRole

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
    
    # Create a new non-solo organization for the user
    new_org = Organization(
        name=f"{current_user.email}'s Organization",
        is_solo=False,
        org_owner=current_user.id
    )
    db.add(new_org)
    db.flush()  # Flush to get the new_org.id for metadata
    
    # Associate the current user as an ADMIN of the new organization
    org_user_link = OrganizationUser(
        user=current_user,
        organization=new_org,
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
