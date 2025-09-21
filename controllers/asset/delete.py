from sqlalchemy.orm import Session
from models.asset import Asset
from models.user import User
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
import os
import logging

logger = logging.getLogger(__name__)

def delete(db: Session, asset_id: int, current_user: User):
    """Delete an asset by ID with ownership/permission checks and remove file from GCP"""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    
    if not asset:
        return False
    
    # Check permissions:
    # - User can delete their own assets
    # - Superadmin/admin can delete any asset
    # - Anonymous assets (user_id is None) can only be deleted by superadmin/admin
    can_delete = False
    
    if asset.user_id is None:
        # Anonymous asset - only superadmin/admin can delete
        can_delete = current_user.role in ["superadmin", "admin"]
    elif asset.user_id == current_user.id or current_user.role in ["superadmin", "admin"]:
        can_delete = True
    
    if not can_delete:
        return False
    
    # First, try to delete the file from GCP
    gcp_deletion_success = False
    try:
        if asset.bucket_name and asset.file_path:
            # Initialize GCP client
            service_account_key = os.getenv("GCP_SERVICE_ACCOUNT_KEY")
            if service_account_key:
                client = storage.Client.from_service_account_json(service_account_key)
                bucket = client.get_bucket(asset.bucket_name)
                blob = bucket.blob(asset.file_path)
                
                # Check if blob exists before trying to delete
                if blob.exists():
                    blob.delete()
                    logger.info(f"Successfully deleted file from GCP: {asset.bucket_name}/{asset.file_path}")
                else:
                    logger.warning(f"File not found in GCP (may have been already deleted): {asset.bucket_name}/{asset.file_path}")
                
                gcp_deletion_success = True
            else:
                logger.error("GCP_SERVICE_ACCOUNT_KEY not configured")
        else:
            logger.warning(f"Asset {asset_id} missing bucket_name or file_path, skipping GCP deletion")
            gcp_deletion_success = True  # Consider this success since there's nothing to delete
            
    except GoogleCloudError as e:
        logger.error(f"GCP deletion failed for asset {asset_id}: {str(e)}")
        # Continue with database deletion even if GCP deletion fails
    except Exception as e:
        logger.error(f"Unexpected error during GCP deletion for asset {asset_id}: {str(e)}")
        # Continue with database deletion even if GCP deletion fails
    
    # Delete the asset record from database
    try:
        db.delete(asset)
        db.commit()
        
        if not gcp_deletion_success:
            logger.warning(f"Asset {asset_id} deleted from database but GCP file deletion failed")
        else:
            logger.info(f"Asset {asset_id} successfully deleted from both database and GCP")
        
        return True
        
    except Exception as e:
        logger.error(f"Database deletion failed for asset {asset_id}: {str(e)}")
        db.rollback()
        return False
