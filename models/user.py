# this file defines all the models realated to managing custom data schemas
from sqlalchemy import Column, String, Integer,func, ForeignKey, DateTime, Boolean
from .base import Base
from sqlalchemy.orm import relationship
from dependencies.enums import RoleEnum
from sqlalchemy import Enum as SQLAlchemyEnum
from datetime import datetime, timedelta

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    confirmed = Column(Boolean, index=True, default=False)
    hashed_password = Column(String)
    tokens = relationship("Token", back_populates="user")
    role = Column(SQLAlchemyEnum(RoleEnum), unique=False, nullable=False)
    organization_associations = relationship("OrganizationUser", back_populates="user", cascade="all, delete-orphan")
    email_confirmations = relationship("EmailConfirmation", back_populates="user", cascade="all, delete-orphan")
    reset_password_requests = relationship("ResetPasswordRequest", back_populates="user", cascade="all, delete-orphan")
    

class EmailConfirmation(Base):
    __tablename__ = "email_confirmations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=2))
    used = Column(Boolean, default=False)
    valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="email_confirmations")

# auth token
class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, index=True)
    expires_at = Column(DateTime)
    user_id = Column(Integer, ForeignKey('users.id'))
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="tokens")


#auth reset token 
class ResetPasswordRequest(Base):
    __tablename__ = "reset_password_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String, unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=2))
    used = Column(Boolean, default=False)
    valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reset_password_requests")


