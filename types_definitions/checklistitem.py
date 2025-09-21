from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class TaskTypeSchema(str, Enum):
    REFERRAL = "REFERRAL"
    SUBSCRIPTION = "SUBSCRIPTION"
    USAGE = "USAGE"
    SOCIAL_SHARE = "SOCIAL_SHARE"
    SURVEY = "SURVEY"
    MILESTONE = "MILESTONE"
    DAILY_LOGIN = "DAILY_LOGIN"
    FEATURE_USAGE = "FEATURE_USAGE"
    OTHER = "OTHER"

class TaskStatusSchema(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

class RewardTypeSchema(str, Enum):
    SUBSCRIPTION_EXTENSION = "SUBSCRIPTION_EXTENSION"
    CREDITS = "CREDITS"
    FEATURES_UNLOCK = "FEATURES_UNLOCK"
    BADGE = "BADGE"
    DISCOUNT = "DISCOUNT"
    OTHER = "OTHER"

class PublicChecklistItem(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    task_type: TaskTypeSchema
    target_count: int
    current_count: int
    is_completed: bool
    status: TaskStatusSchema
    reward_type: RewardTypeSchema
    reward_value: Optional[str] = None
    reward_description: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    campaign_reference: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    progress_percentage: int

    class Config:
        from_attributes = True

class ChecklistItemUpdate(BaseModel):
    increment: Optional[int] = None
    complete: Optional[bool] = None

class ChecklistItemList(BaseModel):
    items: List[PublicChecklistItem]
    total: int 