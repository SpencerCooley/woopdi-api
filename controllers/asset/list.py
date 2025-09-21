from sqlalchemy.orm import Session
from models.asset import Asset
from models.user import User
from typing import Optional

def list_assets(db: Session, current_user: User, skip: int = 0, limit: int = 100, user_id: Optional[int] = None, upload_source: Optional[str] = None):
    """Get a list of assets with pagination and permission filtering"""
    query = db.query(Asset)
    
    # Permission filtering
    if current_user.role in ["superadmin", "admin"]:
        # Superadmin/admin can see all assets or filter by specific user
        if user_id is not None:
            query = query.filter(Asset.user_id == user_id)
    else:
        # Regular users can only see their own assets
        query = query.filter(Asset.user_id == current_user.id)
    
    # Upload source filtering
    if upload_source is not None:
        query = query.filter(Asset.upload_source == upload_source)
    
    # Apply pagination and ordering (newest first)
    assets = query.order_by(Asset.created_at.desc()).offset(skip).limit(limit).all()
    return assets

def count_assets(db: Session, current_user: User, user_id: Optional[int] = None, upload_source: Optional[str] = None):
    """Get total count of assets with permission filtering"""
    query = db.query(Asset)
    
    # Permission filtering (same logic as list_assets)
    if current_user.role in ["superadmin", "admin"]:
        if user_id is not None:
            query = query.filter(Asset.user_id == user_id)
    else:
        query = query.filter(Asset.user_id == current_user.id)
    
    # Upload source filtering
    if upload_source is not None:
        query = query.filter(Asset.upload_source == upload_source)
    
    return query.count() 