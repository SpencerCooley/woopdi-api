from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class PredictionType(str, Enum):
    IMAGE_GENERATION = "IMAGE_GENERATION"
    TEXT_GENERATION = "TEXT_GENERATION"
    AUDIO_GENERATION = "AUDIO_GENERATION"
    VIDEO_GENERATION = "VIDEO_GENERATION"
    IMAGE_PROCESSING = "IMAGE_PROCESSING"
    OTHER = "OTHER"

class CreatePredictionRequest(BaseModel):
    model: str
    prediction_type: PredictionType
    output_asset_id: Optional[int] = None
    meta: Optional[Dict[str, Any]] = None
    processing_time_seconds: Optional[int] = None

class PublicPrediction(BaseModel):
    id: int
    model: str
    prediction_type: PredictionType
    user_id: int
    output_asset_id: Optional[int]
    meta: Optional[Dict[str, Any]]
    processing_time_seconds: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
        use_enum_values = True

class PredictionListResponse(BaseModel):
    predictions: List[PublicPrediction]
    total: int
    skip: int
    limit: int

class DeletePredictionResponse(BaseModel):
    success: bool
    message: str 