"""
User seeding functions for Longivitate.AI

This module contains functions to seed the database with default users.
"""

import os
import sys
from passlib.context import CryptContext

# Add the parent directory to the Python path so we can import our models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import User
from dependencies.enums import RoleEnum

# Initialize the password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_default_users(session):
    """Create default test users"""
    # Hash the password "devpass"
    hashed_password = pwd_context.hash("devpass")
    
    default_users = [
        {'email': 'super@admin.com', 'hashed_password': hashed_password, 'role': RoleEnum.superadmin},
        {'email': 'admin@admin.com', 'hashed_password': hashed_password, 'role': RoleEnum.admin},
        {'email': 'customer@customer.com', 'hashed_password': hashed_password, 'role': RoleEnum.user},
        {'email': 'user@user.com', 'hashed_password': hashed_password, 'role': RoleEnum.user},
        {'email': 'user_subscribed@user.com', 'hashed_password': hashed_password, 'role': RoleEnum.user},
        {'email': 'moderator@usersubscribed.com', 'hashed_password': hashed_password, 'role': RoleEnum.user},
        {'email': 'member1@usersubscribed.com', 'hashed_password': hashed_password, 'role': RoleEnum.user},
        {'email': 'member2@usersubscribed.com', 'hashed_password': hashed_password, 'role': RoleEnum.user},
        {'email': 'member3@usersubscribed.com', 'hashed_password': hashed_password, 'role': RoleEnum.user},
        {'email': 'member4@usersubscribed.com', 'hashed_password': hashed_password, 'role': RoleEnum.user},
    ]
    
    # Combine default users and test users
    all_users = default_users
    
    # Create all users in a single batch to avoid transaction issues
    users_to_create = []
    
    for user_data in all_users:
        # Check if user already exists (handle case where table doesn't exist yet)
        try:
            existing_user = session.query(User).filter(User.email == user_data['email']).first()
            if not existing_user:
                user = User(
                    email=user_data['email'],
                    hashed_password=user_data['hashed_password'],
                    role=user_data['role'],
                    confirmed=True
                )
                users_to_create.append(user)
                print(f"Created user: {user_data['email']} with role: {user_data['role'].value}")
            else:
                print(f"User already exists: {user_data['email']}")
        except Exception as e:
            # If there's any error checking for existing users, create the user anyway
            print(f"Error checking for existing user {user_data['email']}: {e}")
            user = User(
                email=user_data['email'],
                hashed_password=user_data['hashed_password'],
                role=user_data['role'],
                confirmed=True
            )
            users_to_create.append(user)
            print(f"Created user: {user_data['email']} with role: {user_data['role'].value}")
    
    # Add all users at once
    if users_to_create:
        try:
            session.add_all(users_to_create)
            session.flush()  # Flush to catch any constraint violations early
        except Exception as e:
            print(f"Error creating users in batch: {e}")
            session.rollback()
            # Try creating users one by one to identify the problematic one
            for user in users_to_create:
                try:
                    session.add(user)
                    session.flush()
                    print(f"Successfully created user: {user.email}")
                except Exception as individual_error:
                    print(f"Failed to create user {user.email}: {individual_error}")
                    session.rollback() 