from sqlalchemy import Column, String, DateTime, func, ForeignKey, Table, Integer
from sqlalchemy.orm import relationship
from .base import Base
import datetime

class Invitation(Base):
    __tablename__ = 'invitations'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=False)
    inviter_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default='pending', nullable=False)  # pending, accepted, expired
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.utcnow() + datetime.timedelta(days=7))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    organization = relationship("Organization")
    inviter = relationship("User")