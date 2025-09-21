from sqlalchemy.orm import Session
from models.asset import Asset
from models.user import User

def get(db: Session, asset_id: int, current_user: User):
    """Get a single asset by ID with ownership/permission checks"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    
    if not asset:
        return None
    
    # Check permissions:
    # - User can access their own assets
    # - Superadmin/admin can access any asset
    # - Anonymous assets (user_id is None) can only be accessed by superadmin/admin
    if asset.user_id is None:
        # Anonymous asset - only superadmin/admin can access
        if current_user.role in ["superadmin", "admin"]:
            return asset
        else:
            return None
    elif asset.user_id == current_user.id or current_user.role in ["superadmin", "admin"]:
        return asset
    
    # User doesn't have permission to access this asset
    return None
