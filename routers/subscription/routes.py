from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.user import User
from dependencies.dependencies import get_current_user, get_db
from types_definitions.subscription import CreateSubscriptionRequest, CreateSubscriptionResponse, PublicSubscription
import controllers

router = APIRouter(
    prefix="/subscription",
    tags=["Subscription"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=CreateSubscriptionResponse)
def create_subscription(
    subscription_request: CreateSubscriptionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates a new subscription for the user's organization.
    This endpoint handles the entire process of setting up a new paid organization
    and subscribing it to a Stripe plan.
    """
    return controllers.subscription.create(db=db, current_user=current_user, subscription_request=subscription_request)


@router.post("/free", response_model=PublicSubscription)
def create_free_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a free subscription for the authenticated user.
    """
    try:
        subscription = controllers.subscription.create_free_subscription(db, current_user)
        return subscription
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


