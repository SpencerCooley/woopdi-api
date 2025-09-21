from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from types_definitions.asset import PublicAsset, AssetListResponse, DeleteAssetResponse
from dependencies.dependencies import get_db, get_current_user, get_current_user_optional
from sqlalchemy.orm import Session
from models.user import User
import controllers
from typing import Optional
import logging
import asyncio
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from models.asset import Asset
import asyncio
from google.cloud import storage
import uuid, os
from pydantic import BaseModel

router = APIRouter(
    prefix="/asset",
    tags=["Assets"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=AssetListResponse)
async def list_assets(
    skip: int = Query(0, ge=0, description="Number of assets to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of assets to return"),
    user_id: Optional[int] = Query(None, description="Filter by user ID (admin/superadmin only)"),
    upload_source: Optional[str] = Query(None, description="Filter by upload source"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a list of assets with pagination support.
    Users can only see their own assets.
    Admins and superadmins can see all assets or filter by user_id.
    Can be filtered by upload_source (e.g., 'image-generator-face').
    """
    assets = controllers.asset.list_assets(db, current_user, skip=skip, limit=limit, user_id=user_id, upload_source=upload_source)
    total = controllers.asset.count_assets(db, current_user, user_id=user_id, upload_source=upload_source)
    return AssetListResponse(
        assets=assets,
        total=total,
        skip=skip,
        limit=limit
    )

@router.get("/{asset_id}", response_model=PublicAsset)
async def get_asset(
    asset_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific asset by ID.
    Users can only access their own assets.
    Admins and superadmins can access any asset.
    """
    asset = controllers.asset.get(db, asset_id, current_user)
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found or access denied")
    return asset

@router.delete("/{asset_id}", response_model=DeleteAssetResponse)
async def delete_asset(
    asset_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a specific asset by ID.
    Users can only delete their own assets.
    Admins and superadmins can delete any asset.
    """
    success = controllers.asset.delete(db, asset_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found or access denied")
    return DeleteAssetResponse(
        success=True,
        message=f"Asset with ID {asset_id} has been successfully deleted"
    ) 




class UploadAssetResponse(BaseModel):
    gcp_blob_name: str
    message: str
    public_url: str
    asset_id: int  # Add asset_id to the response

# Configure logging
logger = logging.getLogger(__name__)


# Configure logging
logger = logging.getLogger(__name__)

# Add these constants at the top after imports
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit
ALLOWED_CONTENT_TYPES = {
    # Images
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp',
    # Documents
    'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain', 'text/csv', 'application/json', 'application/xml', 'text/xml',
    # Audio
    'audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/m4a',
    # Video
    'video/mp4', 'video/avi', 'video/quicktime', 'video/x-msvideo',
    # Archives
    'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed',
    # Other
    'application/octet-stream'
}
UPLOAD_TIMEOUT = 300  # 5 minutes timeout for GCP upload

async def upload_to_gcp_async(file_content: bytes, destination_blob_name: str, content_type: str) -> str:
    """
    Upload file content directly to GCP bucket asynchronously with timeout
    """
    try:
        # Initialize GCP client
        bucket_name = os.getenv("GCP_BUCKET_NAME")
        service_account_key = os.getenv("GCP_SERVICE_ACCOUNT_KEY")
        
        if not bucket_name:
            raise ValueError("GCP_BUCKET_NAME environment variable not set")
        if not service_account_key:
            raise ValueError("GCP_SERVICE_ACCOUNT_KEY environment variable not set")
        
        logger.info(f"Starting GCP upload for {destination_blob_name}, size: {len(file_content)} bytes")
        
        # Run the GCP upload in a thread pool to avoid blocking
        def _upload_to_gcp():
            # Initialize client with service account JSON file (matching existing pattern)
            client = storage.Client.from_service_account_json(service_account_key)
            bucket = client.get_bucket(bucket_name)
            blob = bucket.blob(destination_blob_name)

            # Upload the file content first (without setting content type)
            blob.upload_from_string(file_content)

            # Then update the content type to the correct type
            blob.content_type = content_type
            blob.patch()  # Update the blob metadata

            return f"https://storage.googleapis.com/{bucket_name}/{destination_blob_name}"
        
        # Run in thread pool with timeout
        loop = asyncio.get_event_loop()
        public_url = await asyncio.wait_for(
            loop.run_in_executor(None, _upload_to_gcp),
            timeout=UPLOAD_TIMEOUT
        )
        
        logger.info(f"Successfully uploaded {destination_blob_name} to GCP")
        return public_url
        
    except asyncio.TimeoutError:
        logger.error(f"GCP upload timeout for {destination_blob_name}")
        raise HTTPException(status_code=504, detail="Upload timeout - please try again with a smaller file")
    except GoogleCloudError as e:
        logger.error(f"GCP upload failed for {destination_blob_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"GCP upload failed: {str(e)}")
    except Exception as e:
        logger.error(f"Upload error for {destination_blob_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")


@router.post("/upload", response_model=UploadAssetResponse)
async def upload_asset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
    file_source: str = Form(...)
):
    """
    Upload a file to GCP bucket, create an Asset record, and return the details.
    Streams file directly to GCP without writing to disk.
    Works for both authenticated and anonymous users.
    Supports various file types including images, documents, audio, video, and archives.
    """
    asset = None
    start_time = asyncio.get_event_loop().time()
    
    try:
        logger.info(f"Starting file upload: {file.filename}, content_type: {file.content_type}")
        
        # Validate file type
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            logger.warning(f"Invalid file type attempted: {file.content_type}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}"
            )

        # Validate filename
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # Generate destination blob name
        ext = os.path.splitext(file.filename)[1].lower()
        if not ext:
            ext = '.jpg'  # Default extension
        destination_blob_name = f"{uuid.uuid4().hex}{ext}"

        logger.info(f"Generated blob name: {destination_blob_name}")
        
        # Read file in chunks to avoid memory issues
        file_chunks = []
        total_size = 0

        # Reset file pointer to beginning
        await file.seek(0)

        # Read file in chunks
        chunk_size = 8192  # 8KB chunks
        chunks_read = 0
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break

            total_size += len(chunk)
            chunks_read += 1

            # Check file size limit
            if total_size > MAX_FILE_SIZE:
                logger.warning(f"File too large: {total_size} bytes (limit: {MAX_FILE_SIZE})")
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
                )

            file_chunks.append(chunk)

        logger.info(f"File read complete: {total_size} bytes in {chunks_read} chunks")

        # Validate that we actually have content
        if total_size == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        # Combine chunks properly
        file_content = b''.join(file_chunks)

        # Upload directly to GCP
        public_url = await upload_to_gcp_async(file_content, destination_blob_name, file.content_type)

        # Create Asset record in database
        bucket_name = os.getenv("GCP_BUCKET_NAME")
        asset = Asset(
            filename=file.filename,
            bucket_name=bucket_name,
            file_path=destination_blob_name,
            content_type=file.content_type,
            file_size=total_size,
            user_id=current_user.id if current_user else None,
            preserve=False,
            public_url=public_url,
            upload_source=file_source,
            meta={
                "original_filename": file.filename,
                "upload_endpoint": "/tools/upload-image",
                "user_type": "authenticated" if current_user else "anonymous",
                "file_size_mb": round(total_size / (1024*1024), 2)
            }
        )
        
        db.add(asset)
        db.commit()
        db.refresh(asset)

        end_time = asyncio.get_event_loop().time()
        duration = round(end_time - start_time, 2)
        
        logger.info(f"Upload completed successfully in {duration}s: {destination_blob_name} ({round(total_size / (1024*1024), 2)}MB)")

        return UploadAssetResponse(
            gcp_blob_name=destination_blob_name,
            message=f"File uploaded successfully ({round(total_size / (1024*1024), 2)}MB)",
            public_url=public_url,
            asset_id=asset.id
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Rollback database transaction if asset was created
        if asset:
            try:
                db.rollback()
            except Exception as rollback_error:
                logger.error(f"Database rollback failed: {rollback_error}")
        
        # Log the error for debugging
        end_time = asyncio.get_event_loop().time()
        duration = round(end_time - start_time, 2)
        logger.error(f"Upload failed after {duration}s: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")
    
    finally:
        # Ensure file is closed
        try:
            await file.close()
        except Exception as close_error:
            logger.warning(f"Error closing file: {close_error}")
