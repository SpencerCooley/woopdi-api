from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime


class CreateSubscriptionRequest(BaseModel):
    payment_method_id: str
    price_id: str
    quantity: int = 1

    @field_validator('payment_method_id')
    @classmethod
    def payment_method_id_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('payment_method_id cannot be empty')
        return v

    @field_validator('price_id')
    @classmethod
    def price_id_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('price_id cannot be empty')
        return v
    
    @field_validator('quantity')
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v < 1:
            raise ValueError('quantity must be at least 1')
        return v

class UpdateSubscriptionObject(BaseModel):
    status: Optional[str] = None
    price_id: Optional[str] = None
    cancel_subscription: Optional[bool] = False

class PublicSubscription(BaseModel):
    id: int
    organization_id: int
    stripe_subscription_id: str
    status: str
    price_id: str
    created_at: datetime
    updated_at: datetime
    restrict_access_on: Optional[datetime] = None

    class Config:
        from_attributes = True

class SubscriptionListResponse(BaseModel):
    subscriptions: List[PublicSubscription]
    total: int
    skip: int
    limit: int

class DeleteSubscriptionResponse(BaseModel):
    success: bool
    message: str

class SubscriptionStatusResponse(BaseModel):
    has_active_subscription: bool
    current_subscription: Optional[PublicSubscription] = None

class CreateSubscriptionResponse(BaseModel):
    subscription: PublicSubscription
    client_secret: Optional[str] = None 