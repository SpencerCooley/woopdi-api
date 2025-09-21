import sys
import os

# Add the /app directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from main import app
from dependencies.dependencies import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic import command
from alembic.config import Config
from sqlalchemy.exc import ProgrammingError
from models.base import Base
from sqlalchemy import text
from passlib.context import CryptContext

# Import models for test helpers
from models.user import User
from models.organization import Organization, OrganizationUser, Subscription
from dependencies.enums import RoleEnum
from types_definitions.organization_user import OrganizationUserRole

# Use test database
os.environ["DATABASE_URL"] = "postgresql://test_user:test_password@test_db:5432/test_db"

# Create test database engine
TEST_DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Password context for creating test users
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def reset_database():
    """Reset database by dropping all tables and running migrations"""
    try:
        alembic_cfg = Config("alembic.ini")

        with engine.connect() as connection:
            connection.execution_options(isolation_level="AUTOCOMMIT")

            # Drop all tables
            connection.execute(text("DROP SCHEMA public CASCADE;"))
            connection.execute(text("CREATE SCHEMA public;"))
            print("Dropped and recreated public schema")

        # Apply all migrations
        command.upgrade(alembic_cfg, "head")
        print("Applied all migrations")
    except Exception as e:
        print(f"Error resetting database: {e}")
        # If we can't reset properly, try a simpler approach
        try:
            with engine.connect() as connection:
                connection.execution_options(isolation_level="AUTOCOMMIT")
                connection.execute(text("DROP SCHEMA public CASCADE;"))
                connection.execute(text("CREATE SCHEMA public;"))
                print("Fallback: Dropped and recreated public schema")
        except Exception as e2:
            print(f"Fallback failed: {e2}")
            raise


# Override FastAPI's get_db() dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    """Set up test database with migrations before running every test"""
    reset_database()
    yield
    # Clean up after all tests
    reset_database()


@pytest.fixture(scope="function")
def db():
    """Creates a new database session for each test"""
    session = TestingSessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="function")
def client():
    """FastAPI TestClient using the test database"""
    return TestClient(app)


# Helper fixtures for creating test data
@pytest.fixture
def create_test_user():
    """Factory fixture for creating test users"""
    def _create_user(db, email="test@example.com", password="testpass123", role=RoleEnum.user):
        hashed_password = pwd_context.hash(password)
        user = User(
            email=email,
            hashed_password=hashed_password,
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    return _create_user

@pytest.fixture
def test_user(db, create_test_user):
    """Creates a single test user for tests that need one"""
    return create_test_user(db, "testuser@example.com", "testpass123", RoleEnum.user)

@pytest.fixture
def admin_user(db, create_test_user):
    """Creates an admin user for tests that need admin privileges"""
    return create_test_user(db, "admin@example.com", "adminpass123", RoleEnum.admin)


@pytest.fixture
def create_test_subscription():
    """Factory fixture for creating test subscriptions"""
    def _create_subscription(db, user_id, plan_id="price_test_premium", status="active"):
        from models.user import Subscription
        
        # Generate a unique stripe subscription ID for testing
        import uuid
        stripe_subscription_id = f"sub_test_{uuid.uuid4().hex[:8]}"
        
        subscription = Subscription(
            user_id=user_id,
            stripe_subscription_id=stripe_subscription_id,
            status=status,
            plan_id=plan_id
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        return subscription
    return _create_subscription


@pytest.fixture
def create_test_auth_headers():
    """
    Factory fixture for creating JWT auth headers for a test user.
    """
    def _create_headers(db, email="test@example.com", password="testpass123", role=RoleEnum.user):
        from controllers.user.retrieve_token import retrieve_token

        class Credentials:
            def __init__(self, email, password):
                self.email = email
                self.password = password

        # 1. Create user
        hashed_password = pwd_context.hash(password)
        user = User(email=email, hashed_password=hashed_password, role=role)
        db.add(user)
        db.commit()
        db.refresh(user)

        # 2. Generate token (mimicking login)
        credentials = Credentials(email, password)
        token_data = retrieve_token(db, credentials)
        token = token_data['token']

        # 3. Return auth headers
        return {"Authorization": f"Bearer {token}"}
    return _create_headers


# Helper function for creating auth headers for any user
def get_user_auth_headers(db, user, password="devpass"):
    """
    Helper function to create JWT auth headers for a user.
    Takes a user object and password, returns auth headers.
    """
    from controllers.user.retrieve_token import retrieve_token

    class Credentials:
        def __init__(self, email, password):
            self.email = user.email
            self.password = password

    # Generate token (mimicking login)
    credentials = Credentials(user.email, password)
    token_data = retrieve_token(db, credentials)
    token = token_data['token']

    # Return auth headers
    return {"Authorization": f"Bearer {token}"}


# Seed fixture for organizations and users
@pytest.fixture(scope="function")
def seed_test_organizations_and_users(db):
    """
    Seeds the database with a consistent set of organizations and users for testing.
    This mirrors the development seed structure for consistency.
    
    Creates:
    - Multiple users with different roles (admin, moderator, member)
    - Multiple organizations with different configurations
    - Proper organization memberships
    - Subscriptions for non-solo organizations
    """
    # Create users if they don't exist (mirroring seed/users.py)
    default_users = [
        {'email': 'super@admin.com', 'role': RoleEnum.superadmin},
        {'email': 'admin@admin.com', 'role': RoleEnum.admin},
        {'email': 'customer@customer.com', 'role': RoleEnum.user},
        {'email': 'user@user.com', 'role': RoleEnum.user},
        {'email': 'user_subscribed@user.com', 'role': RoleEnum.user},
        {'email': 'moderator@usersubscribed.com', 'role': RoleEnum.user},
        {'email': 'member1@usersubscribed.com', 'role': RoleEnum.user},
        {'email': 'member2@usersubscribed.com', 'role': RoleEnum.user},
        {'email': 'member3@usersubscribed.com', 'role': RoleEnum.user},
        {'email': 'member4@usersubscribed.com', 'role': RoleEnum.user},
    ]
    
    # Create all users
    for user_data in default_users:
        user = db.query(User).filter(User.email == user_data['email']).first()
        if not user:
            user = User(
                email=user_data['email'],
                hashed_password=pwd_context.hash("devpass"),
                role=user_data['role'],
                confirmed=True
            )
            db.add(user)
    db.commit()
    
    # Create solo organizations for all users (mirroring seed/organizations.py)
    for user_data in default_users:
        user = db.query(User).filter(User.email == user_data['email']).first()
        if not db.query(Organization).join(OrganizationUser).filter(
            OrganizationUser.user_id == user.id, 
            Organization.is_solo == True
        ).first():
            solo_org = Organization(name=f"{user.email}'s solo org", is_solo=True, org_owner=user.id)
            db.add(solo_org)
            db.flush()
            org_user = OrganizationUser(
                user_id=user.id, 
                organization_id=solo_org.id, 
                role=OrganizationUserRole.ADMIN
            )
            db.add(org_user)
            print(f"Created solo organization for {user.email}")
    
    # Create non-solo organization and subscription for user_subscribed@user.com
    subscribed_user = db.query(User).filter(User.email == 'user_subscribed@user.com').first()
    if not db.query(Organization).join(OrganizationUser).filter(
        OrganizationUser.user_id == subscribed_user.id, 
        Organization.is_solo == False
    ).first():
        non_solo_org = Organization(name="Subscribed Org", is_solo=False, org_owner=subscribed_user.id)
        db.add(non_solo_org)
        db.flush()
        org_user = OrganizationUser(
            user_id=subscribed_user.id, 
            organization_id=non_solo_org.id, 
            role=OrganizationUserRole.ADMIN
        )
        db.add(org_user)
        print(f"Created non-solo organization for {subscribed_user.email}")

        # Add subscription
        subscription = Subscription(
            organization_id=non_solo_org.id,
            stripe_subscription_id="sub_placeholder_123",
            status="active",
            price_id="price_placeholder_123"
        )
        db.add(subscription)
        print(f"Created subscription for {subscribed_user.email}")

        # Add members to the non-solo organization
        member_emails = [
            'member1@usersubscribed.com',
            'member2@usersubscribed.com',
            'member3@usersubscribed.com',
            'member4@usersubscribed.com',
            'moderator@usersubscribed.com'
        ]
        for email in member_emails:
            member = db.query(User).filter(User.email == email).first()
            role = OrganizationUserRole.MODERATOR if email == 'moderator@usersubscribed.com' else OrganizationUserRole.MEMBER
            org_user = OrganizationUser(
                user_id=member.id, 
                organization_id=non_solo_org.id, 
                role=role
            )
            db.add(org_user)
            print(f"Added {email} to Subscribed Org with role {role.value}")

    # Create non-solo organization and subscription for user_subscribed2@user.com
    # We'll create a second user for this organization
    user_subscribed2 = db.query(User).filter(User.email == 'user_subscribed2@user.com').first()
    if not user_subscribed2:
        user_subscribed2 = User(
            email='user_subscribed2@user.com',
            hashed_password=pwd_context.hash("devpass"),
            role=RoleEnum.user,
            confirmed=True
        )
        db.add(user_subscribed2)
        db.flush()
    
    if not db.query(Organization).join(OrganizationUser).filter(
        OrganizationUser.user_id == user_subscribed2.id, 
        Organization.is_solo == False
    ).first():
        non_solo_org2 = Organization(name="Subscribed Org 2", is_solo=False, org_owner=user_subscribed2.id)
        db.add(non_solo_org2)
        db.flush()
        org_user = OrganizationUser(
            user_id=user_subscribed2.id, 
            organization_id=non_solo_org2.id, 
            role=OrganizationUserRole.ADMIN
        )
        db.add(org_user)
        print(f"Created non-solo organization for {user_subscribed2.email}")

        # Add subscription
        subscription = Subscription(
            organization_id=non_solo_org2.id,
            stripe_subscription_id="sub_placeholder_1243",
            status="active",
            price_id="price_placeholder_123"
        )
        db.add(subscription)
        print(f"Created subscription for {user_subscribed2.email}")

        # Add members to the non-solo organization
        member_emails = [
            'member3@usersubscribed.com',
            'member4@usersubscribed.com'
        ]
        for email in member_emails:
            member = db.query(User).filter(User.email == email).first()
            org_user = OrganizationUser(
                user_id=member.id, 
                organization_id=non_solo_org2.id, 
                role=OrganizationUserRole.MEMBER
            )
            db.add(org_user)
            print(f"Added {email} to Subscribed Org 2")

    db.commit()
    
    # Return the created objects for easy access in tests
    return {
        'users': [db.query(User).filter(User.email == email).first() for email in [
            'super@admin.com', 'admin@admin.com', 'customer@customer.com', 
            'user@user.com', 'user_subscribed@user.com', 'moderator@usersubscribed.com',
            'member1@usersubscribed.com', 'member2@usersubscribed.com', 
            'member3@usersubscribed.com', 'member4@usersubscribed.com'
        ]],
        'admin_user': db.query(User).filter(User.email == 'admin@admin.com').first(),
        'superadmin_user': db.query(User).filter(User.email == 'super@admin.com').first(),
        'user_subscribed': db.query(User).filter(User.email == 'user_subscribed@user.com').first(),
        'user_subscribed2': user_subscribed2,
        'moderator_user': db.query(User).filter(User.email == 'moderator@usersubscribed.com').first(),
        'member1': db.query(User).filter(User.email == 'member1@usersubscribed.com').first(),
        'member2': db.query(User).filter(User.email == 'member2@usersubscribed.com').first(),
        'member3': db.query(User).filter(User.email == 'member3@usersubscribed.com').first(),
        'member4': db.query(User).filter(User.email == 'member4@usersubscribed.com').first(),
        'organization': db.query(Organization).filter(Organization.name == "Subscribed Org").first(),
        'organization2': db.query(Organization).filter(Organization.name == "Subscribed Org 2").first(),
        'solo_organization': db.query(Organization).join(OrganizationUser).filter(
            OrganizationUser.user_id == db.query(User).filter(User.email == 'admin@admin.com').first().id, 
            Organization.is_solo == True
        ).first()
    }
