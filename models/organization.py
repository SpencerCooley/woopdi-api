from sqlalchemy import Column, String, Boolean, Integer, DateTime, func, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from enum import Enum
from .base import Base
from types_definitions.organization_user import OrganizationUserRole

# add roles as needed. 
# keeping roles simple with middleware based permissions on endpoints
# a little chaotic, but better to keep it simple than to make some complicated policy framework. 

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    is_solo = Column(Boolean, default=True, nullable=False)
    org_owner = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    stripe_customer_id = Column(String, unique=True, nullable=True)

    # Relationships
    members = relationship("OrganizationUser", back_populates="organization", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="organization")
    subscriptions = relationship("Subscription", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}')>"

class OrganizationUser(Base):
    __tablename__ = "organization_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    role = Column(SQLAlchemyEnum(OrganizationUserRole), nullable=False, default=OrganizationUserRole.MEMBER)

    # Relationships
    user = relationship("User", back_populates="organization_associations")
    organization = relationship("Organization", back_populates="members")

    def __repr__(self):
        return f"<OrganizationUser(user_id={self.user_id}, organization_id={self.organization_id}, role='{self.role.value}')>"

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    stripe_subscription_id = Column(String, unique=True, nullable=False)
    status = Column(String, nullable=False)
    price_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    restrict_access_on = Column(DateTime, nullable=True)

    organization = relationship("Organization", back_populates="subscriptions")
