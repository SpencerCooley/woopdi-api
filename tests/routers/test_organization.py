import pytest
from fastapi.testclient import TestClient
from tests.conftest import seed_test_organizations_and_users, get_user_auth_headers

# Import the app from main to ensure all routers are loaded
from main import app

client = TestClient(app)

def test_list_organizations_as_superadmin(client, db, seed_test_organizations_and_users):
    """Test listing organizations as superadmin"""
    # Get the superadmin user from the seeded data
    superadmin_user = seed_test_organizations_and_users['superadmin_user']
    
    # Get auth headers for superadmin
    headers = get_user_auth_headers(db, superadmin_user)
    
    # Make the request
    response = client.get("/organizations/", headers=headers)
    
    # Check response
    assert response.status_code == 200
    # Should return at least one organization (from the seed data)
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

def test_list_organizations_as_admin(client, db, seed_test_organizations_and_users):
    """Test listing organizations as admin"""
    # Get the admin user from the seeded data
    admin_user = seed_test_organizations_and_users['admin_user']
    
    # Get auth headers for admin
    headers = get_user_auth_headers(db, admin_user)
    
    # Make the request
    response = client.get("/organizations/", headers=headers)
    
    # Check response
    assert response.status_code == 200
    # Should return at least one organization (from the seed data)
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

def test_list_organizations_unauthorized(client, db, seed_test_organizations_and_users):
    """Test unauthorized access to organization listing"""
    # Get a regular user from the seeded data
    regular_user = seed_test_organizations_and_users['user_subscribed']
    
    # Get auth headers for regular user
    headers = get_user_auth_headers(db, regular_user)
    
    # Make the request
    response = client.get("/organizations/", headers=headers)
    
    # Should fail with 403
    assert response.status_code == 403
