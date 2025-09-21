from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class PublicAsset(BaseModel):
    id: int
    filename: str
    bucket_name: str
    file_path: str
    content_type: Optional[str]
    file_size: Optional[int]
    original_asset_id: Optional[int]
    user_id: Optional[int]
    preserve: bool
    expires_at: Optional[datetime]
    meta: Optional[Dict[str, Any]]
    public_url: Optional[str]
    checksum: Optional[str]
    upload_source: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class AssetListResponse(BaseModel):
    assets: List[PublicAsset]
    total: int
    skip: int
    limit: int

class DeleteAssetResponse(BaseModel):
    success: bool
    message: str 