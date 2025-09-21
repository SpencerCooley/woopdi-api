from sqlalchemy import Column, String, Integer, DateTime, func, Boolean, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from .base import Base

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    
    # File identification
    filename = Column(String, nullable=False)  # Original filename
    bucket_name = Column(String, nullable=False)  # GCP bucket name
    file_path = Column(String, nullable=False)  # Full path in bucket (e.g., "uploads/2024/01/file.jpg")
    content_type = Column(String, nullable=True)  # MIME type (e.g., "image/jpeg", "application/pdf")
    file_size = Column(BigInteger, nullable=True)  # File size in bytes
    
    # Asset relationships and variations
    original_asset_id = Column(Integer, ForeignKey('assets.id'), nullable=True)  # Reference to original if this is a variation
    original_asset = relationship("Asset", remote_side=[id], backref="variations")
    
    # Ownership and access
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # Owner of the asset (nullable for anonymous uploads)
    user = relationship("User", backref="assets")
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=True)
    organization = relationship("Organization", back_populates="assets")
    
    # Lifecycle management
    preserve = Column(Boolean, default=False, nullable=False)  # Whether to preserve or allow deletion
    expires_at = Column(DateTime, nullable=True)  # When temporary assets should be disposed of
    
    # Metadata and processing info
    meta = Column(JSONB, nullable=True)  # Metadata like processing parameters, AI models used, etc.
    
    # Additional useful fields
    public_url = Column(String, nullable=True)  # Public URL if available
    checksum = Column(String, nullable=True)  # File checksum for integrity verification
    upload_source = Column(String, nullable=True)  # Source of upload (e.g., "api", "batch_process", "ai_generation")
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<Asset(id={self.id}, filename='{self.filename}', user_id={self.user_id})>"
