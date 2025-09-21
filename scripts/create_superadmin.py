import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import argparse

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.user import User
from dependencies.enums import RoleEnum
from utils.password import get_password_hash
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable not set.")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_superadmin(email, password):
    """Creates a superadmin user without an organization."""
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"Error: User with email '{email}' already exists.")
            return

        # Create new superadmin user
        hashed_password = get_password_hash(password)
        superadmin = User(
            email=email,
            hashed_password=hashed_password,
            role=RoleEnum.superadmin
        )
        db.add(superadmin)
        db.commit()
        print(f"Successfully created superadmin: {email}")

    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a new superadmin user.")
    parser.add_argument("email", type=str, help="Email address for the new superadmin.")
    parser.add_argument("password", type=str, help="Password for the new superadmin.")
    args = parser.parse_args()

    create_superadmin(args.email, args.password) 