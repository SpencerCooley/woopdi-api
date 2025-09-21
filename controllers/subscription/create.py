from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models.user import User
from models.organization import Organization, OrganizationUser, Subscription
from types_definitions.subscription import CreateSubscriptionRequest
import stripe
import os
from dotenv import load_dotenv
from fastapi import HTTPException
from types_definitions.organization_user import OrganizationUserRole

# Load environment variables and configure Stripe
load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create(db: Session, current_user: User, subscription_request: CreateSubscriptionRequest):
    """
    Creates a new non-solo organization with its own Stripe customer and subscription.
    """
    # Create a new non-solo organization that will be the paid organization
    new_org = Organization(
        name=f"{current_user.email}'s Organization",
        is_solo=False
    )
    db.add(new_org)
    db.flush() # Flush to get the new_org.id for metadata

    try:
        # Create a new Stripe customer for this specific organization
        customer = stripe.Customer.create(
            email=current_user.email,
            metadata={'organization_id': new_org.id}
        )
        stripe_customer_id = customer.id

        # Save the new customer ID to the organization
        new_org.stripe_customer_id = stripe_customer_id
        db.add(new_org)

        # Associate the current user as an ADMIN of the new organization
        org_user_link = OrganizationUser(
            user=current_user,
            organization=new_org,
            role=OrganizationUserRole.ADMIN
        )
        db.add(org_user_link)

        # Attach payment method to the new customer
        stripe.PaymentMethod.attach(
            subscription_request.payment_method_id,
            customer=stripe_customer_id,
        )

        # Set as default payment method
        stripe.Customer.modify(
            stripe_customer_id,
            invoice_settings={
                'default_payment_method': subscription_request.payment_method_id,
            },
        )

        # Create the Stripe subscription for the new customer
        stripe_subscription = stripe.Subscription.create(
            customer=stripe_customer_id,
            items=[{'price': subscription_request.price_id, 'quantity': subscription_request.quantity}],
            payment_behavior='error_if_incomplete',
            payment_settings={'save_default_payment_method': 'on_subscription'},
            expand=['latest_invoice'],
            metadata={'organization_id': new_org.id}
        )

        # Save subscription to our database
        db_subscription = Subscription(
            organization_id=new_org.id,
            stripe_subscription_id=stripe_subscription.id,
            status=stripe_subscription.status,
            price_id=subscription_request.price_id
        )
        db.add(db_subscription)
        db.commit()
        db.refresh(db_subscription)

        return {
            'subscription': db_subscription,
            'client_secret': None
        }

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="A subscription already exists for this organization.")
    except stripe.error.StripeError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")