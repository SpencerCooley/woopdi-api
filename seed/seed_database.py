#!/usr/bin/env python3
"""
Database seeding script for Longivitate.AI

This script seeds the database with default test users and other initial data.
Run this after running migrations to populate the database with test data.

Usage:
    python seed_database.py
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the Python path so we can import our models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import seeding functions
from seed.users import create_default_users
from seed.organizations import create_organizations_and_subscriptions

def get_database_url():
    """Get database URL from environment variables"""
    # First try to get the full DATABASE_URL (used in Docker)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    
    # If DATABASE_URL is not set, construct it from individual components
    postgres_user = os.getenv("POSTGRES_USER", "postgres")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "password")
    postgres_db = os.getenv("POSTGRES_DB", "longivitate_db")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    
    # For local development, use localhost; for Docker, use 'db'
    postgres_host = "localhost"
    if os.getenv("DOCKER_ENV") or os.path.exists("/.dockerenv"):
        postgres_host = "db"
    
    return f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"

def main():
    """Main seeding function"""
    try:
        # Create database engine and session
        database_url = get_database_url()
        print(f"Connecting to database...")
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        print("Starting database seeding...")
        
        # Create default users first (subscriptions depend on users existing)
        print("\n--- Creating Users ---")
        create_default_users(session)
        session.commit()
        print("Users committed to database.")

        # Create organizations and subscriptions
        print("\n--- Creating Organizations and Subscriptions ---")
        create_organizations_and_subscriptions(session)
        
        # Commit all changes
        session.commit()
        print("\nDatabase seeding completed successfully!")
        
    except Exception as e:
        print(f"Error during database seeding: {e}")
        if 'session' in locals():
            session.rollback()
        sys.exit(1)
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    main()