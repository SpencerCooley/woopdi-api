import pytest
from datetime import datetime, timedelta
from models.user import User
from models.user import Token
from dependencies.enums import RoleEnum
from unittest.mock import patch

@patch('services.email_service.EmailService.notify')
def test_signup_success(mock_notify, client, db):
    """Test successful user registration"""
    response = client.post(
        "/user",
        json={"email": "test@example.com", "password": "testpass123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    # Should match PublicUser model
    expected_keys = {"id", "email", "role"}
    assert set(data.keys()) == expected_keys
    assert data["email"] == "test@example.com"
    assert data["role"] == "user"  # Should default to user
    
    # Verify user was created in database
    user = db.query(User).filter(User.email == "test@example.com").first()
    assert user is not None
    assert user.email == "test@example.com"
    assert user.role.value == "user"  # Role is an enum

def test_signup_duplicate_email(client, db, create_test_user):
    """Test registration with existing email"""
    # Create initial user
    create_test_user(db, "duplicate@example.com", "testpass123")
    
    # Try to create user with same email
    response = client.post(
        "/user/",
        json={"email": "duplicate@example.com", "password": "different123"}
    )
    
    assert response.status_code == 409  
    assert f"User with this email already exists." in response.json()["detail"]

def test_login_success(client, db, create_test_user):
    """Test successful login with valid credentials"""
    # Create a test user
    user = create_test_user(db, "logintest@example.com", "testpass123")
    
    response = client.post(
        "/auth/login",
        json={"email": "logintest@example.com", "password": "testpass123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert isinstance(data["token"], str)
    assert len(data["token"]) > 0  # Token should not be empty

def test_login_invalid_email(client, db):
    """Test login with non-existent email"""
    response = client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "testpass123"}
    )
    
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]

def test_login_invalid_password(client, db, create_test_user):
    """Test login with wrong password"""
    # Create a test user
    create_test_user(db, "wrongpass@example.com", "correctpass123")
    
    response = client.post(
        "/auth/login",
        json={"email": "wrongpass@example.com", "password": "wrongpass123"}
    )
    
    assert response.status_code == 401
    assert "email or password is invalid" in response.json()["detail"]

def test_protected_route_with_valid_token(client, db, create_test_user):
    """Test accessing protected route with valid token"""
    # Create a test user
    user = create_test_user(db, "protectedtest@example.com", "testpass123")
    
    # Login and get token
    login_response = client.post(
        "/auth/login",
        json={"email": "protectedtest@example.com", "password": "testpass123"}
    )

    assert login_response.status_code == 200
    token = login_response.json()["token"]

    # Try to access protected route
    response = client.get(
        "/user/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    # Should match PublicUser model
    expected_keys = {"id", "email", "role"}
    assert set(data.keys()) == expected_keys
    assert data["email"] == "protectedtest@example.com"
    assert data["role"] == "user"
    assert data["id"] == user.id

def test_protected_route_without_token(client, db):
    """Test accessing protected route without token"""
    response = client.get("/user/me")
    
    assert response.status_code == 401

def test_protected_route_with_invalid_token(client, db):
    """Test accessing protected route with invalid token"""
    response = client.get(
        "/user/me",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    
    assert response.status_code == 401

def test_login_seeded_users_success(client, db, create_test_user):
    """Test login with various user roles"""
    # Create users with different roles
    regular_user = create_test_user(db, "user@user.com", "devpass", RoleEnum.user)
    admin_user = create_test_user(db, "admin@admin.com", "devpass", RoleEnum.admin)
    
    
    # Test regular user login
    response = client.post(
        "/auth/login",
        json={"email": "user@user.com", "password": "devpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert isinstance(data["token"], str)
    
    # Test admin login
    response = client.post(
        "/auth/login",
        json={"email": "admin@admin.com", "password": "devpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert isinstance(data["token"], str)

def test_login_invalid_credentials(client, db):
    """Test login with wrong password"""
    response = client.post(
        "/auth/login",
        json={"email": "super@admin.com", "password": "wrongpass"}
    )
    
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()

def test_login_nonexistent_user(client, db):
    """Test login attempt with email that doesn't exist in the system"""
    response = client.post(
        "/auth/login",
        json={"email": "notauser@fake.com", "password": "anypassword"}
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

def test_protected_route_with_expired_token(client, db, create_test_user):
    """Test accessing protected route with expired token"""
    # Create a test user
    user = create_test_user(db, "expiredtest@example.com", "testpass123")
    
    # Login and get token
    login_response = client.post(
        "/auth/login",
        json={"email": "expiredtest@example.com", "password": "testpass123"}
    )
    
    assert login_response.status_code == 200
    token = login_response.json()["token"]

    # Manually expire the token in the database
    token_obj = db.query(Token).filter(Token.token == token).first()
    assert token_obj is not None
    
    # Set expiration to past date
    token_obj.expires_at = datetime.utcnow() - timedelta(hours=1)
    db.commit()

    # Try to access protected route with expired token
    response = client.get(
        "/user/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401

def test_protected_route_with_inactive_token(client, db, create_test_user):
    """Test accessing protected route with inactive token"""
    # Create a test user
    user = create_test_user(db, "inactivetest@example.com", "testpass123")
    
    # Login and get token
    login_response = client.post(
        "/auth/login",
        json={"email": "inactivetest@example.com", "password": "testpass123"}
    )
    
    assert login_response.status_code == 200
    token = login_response.json()["token"]

    # Manually deactivate the token in the database
    token_obj = db.query(Token).filter(Token.token == token).first()
    assert token_obj is not None
    
    # Set token as inactive
    token_obj.is_active = False
    db.commit()

    # Try to access protected route with inactive token
    response = client.get(
        "/user/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
