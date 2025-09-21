from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import User, Organization, OrganizationUser,  EmailConfirmation
from types_definitions.user import CreateUserObject
from utils.password import get_password_hash
from utils.token import generate_secure_token
from services.email_service import woopdi_mail
import stripe
from fastapi import HTTPException
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

def create(db: Session, user: CreateUserObject, role: str = "user"):
    try:
        # Determine if the user should be automatically confirmed
        is_admin_role = role in ["admin", "superadmin"]
        
        # Create the User
        db_user = User(
            email=user.email,
            hashed_password=get_password_hash(user.password),
            role=role,
            confirmed=is_admin_role
        )
        db.add(db_user)
        db.flush()

        # For 'user' roles, create a Stripe customer and both solo and non-solo organizations.
        if not is_admin_role:
            # Initialize Stripe with API key if not already done
            stripe.api_key = _get_stripe_api_key()

            # 1. Create the Stripe Customer for solo organization
            try:
                solo_stripe_customer = stripe.Customer.create(
                    email=user.email,
                    name=f"{user.email} - SOLO",
                    metadata={"role": role, "org_type": "solo"}
                )
            except stripe.error.StripeError as e:
                if "email" in str(e).lower() and "already exists" in str(e).lower():
                    # If customer with this email already exists, create with a unique email
                    import uuid
                    unique_suffix = str(uuid.uuid4())[:8]
                    unique_email = f"{user.email.split('@')[0]}+solo+{unique_suffix}@{user.email.split('@')[1]}"
                    solo_stripe_customer = stripe.Customer.create(
                        email=unique_email,
                        name=f"{user.email} - SOLO",  # Keep original name
                        metadata={"role": role, "org_type": "solo", "original_email": user.email}
                    )
                else:
                    raise e

            # 2. Create the solo Organization for the user
            db_solo_organization = Organization(
                name=f"{db_user.email}'s SOLO Team",
                is_solo=True,
                org_owner=db_user.id,
                stripe_customer_id=solo_stripe_customer.id
            )
            db.add(db_solo_organization)
            db.flush()

            # 3. Link the user to the solo organization with an ADMIN role
            db_solo_org_user_link = OrganizationUser(
                user_id=db_user.id,
                organization_id=db_solo_organization.id,
                role=OrganizationUserRole.ADMIN
            )
            db.add(db_solo_org_user_link)

            # 4. Create the Stripe Customer for non-solo organization
            try:
                non_solo_stripe_customer = stripe.Customer.create(
                    email=user.email,
                    name=f"{user.email} - TEAM",
                    metadata={"role": role, "org_type": "team"}
                )
            except stripe.error.StripeError as e:
                if "email" in str(e).lower() and "already exists" in str(e).lower():
                    # If customer with this email already exists, create with a unique email
                    import uuid
                    unique_suffix = str(uuid.uuid4())[:8]
                    unique_email = f"{user.email.split('@')[0]}+team+{unique_suffix}@{user.email.split('@')[1]}"
                    non_solo_stripe_customer = stripe.Customer.create(
                        email=unique_email,
                        name=f"{user.email} - TEAM",  # Keep original name
                        metadata={"role": role, "org_type": "team", "original_email": user.email}
                    )
                else:
                    raise e

            # 5. Create the non-solo Organization for the user
            db_non_solo_organization = Organization(
                name=f"{db_user.email}'s Team",
                is_solo=False,
                org_owner=db_user.id,
                stripe_customer_id=non_solo_stripe_customer.id
            )
            db.add(db_non_solo_organization)
            db.flush()

            # 6. Link the user to the non-solo organization with an ADMIN role
            db_non_solo_org_user_link = OrganizationUser(
                user_id=db_user.id,
                organization_id=db_non_solo_organization.id,
                role=OrganizationUserRole.ADMIN
            )
            db.add(db_non_solo_org_user_link)

            # 4. Create confirmation token and send email
            confirmation_token = generate_secure_token()
            db_token = EmailConfirmation(user_id=db_user.id, token=confirmation_token)
            db.add(db_token)
            
            # This should be an absolute URL to your frontend confirmation page
            client_url = os.getenv("WEB_CLIENT_URL", "http://localhost:3000")
            confirmation_url = f"{client_url}/confirm-email?token={confirmation_token}"
            
            # this is where it is failing 
            print("attempting to send the confirmation email")
            print(db_user.email)
            print(confirmation_url)

            woopdi_mail.notify(
                template_name='signup_confirmation',
                recipient_email=db_user.email,
                params={'confirmation_url': confirmation_url, 'email': db_user.email}
            )

        # 5. Commit everything in a single transaction
        db.commit()
        db.refresh(db_user)
        
        return db_user
        
    except IntegrityError as e:
        db.rollback()
        # Provide more specific error information
        error_detail = str(e).lower()
        if "email" in error_detail and "already exists" in error_detail:
            raise HTTPException(status_code=409, detail="User with this email already exists.")
        elif "unique constraint" in error_detail:
            raise HTTPException(status_code=409, detail="A record with this information already exists.")
        else:
            raise HTTPException(status_code=409, detail=f"Database integrity error: {str(e)}")
    except stripe.error.StripeError as e:
        # No need to rollback if Stripe fails first
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
