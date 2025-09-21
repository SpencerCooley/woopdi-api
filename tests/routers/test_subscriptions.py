from unittest.mock import patch
from models import User, Organization, Subscription
from dependencies.dependencies import get_db
import pytest
from fastapi import HTTPException
from types_definitions.subscription import CreateSubscriptionRequest
from dependencies.enums import RoleEnum
from passlib.context import CryptContext

def test_create_paid_subscription_without_existing_user(client, db):
    """
    Test attempting to create a paid subscription for a user that doesn't exist.
    """
    # Create headers with a non-existent user
    from dependencies.enums import RoleEnum
    from passlib.context import CryptContext
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Try to create a subscription without creating the user first
    headers = {"Authorization": "Bearer fake_token_here"}
    
    # Attempt to create a paid subscription
    subscription_request = CreateSubscriptionRequest(
        payment_method_id="pm_test123",
        price_id="price_test_premium",
        quantity=1
    )
    
    response = client.post(
        "/subscription/",
        json=subscription_request.dict(),
        headers=headers
    )
    
    # Should fail with 401 (unauthorized) because user doesn't exist
    assert response.status_code == 401


@patch('services.email_service.EmailService.notify')
def test_create_free_subscription_when_disabled(mock_email_notify, client, db, create_test_auth_headers):
    """
    Test creating a free subscription when the system setting is disabled.
    """
    # Temporarily disable free subscriptions
    from config.system_settings import SystemSettings
    original_setting = SystemSettings.AUTO_CREATE_FREE_SUBSCRIPTION
    SystemSettings.AUTO_CREATE_FREE_SUBSCRIPTION = False

    try:
        # Create authenticated headers (this creates the user and returns auth headers)
        headers = create_test_auth_headers(db, "disabled_free_user@example.com", "devpass", RoleEnum.user)

        # Try to create a free subscription
        response = client.post(
            "/subscription/free",
            headers=headers
        )

        # Should fail with 400 because free subscriptions are disabled
        assert response.status_code == 400
        assert "Free subscriptions are not enabled" in response.json()["detail"]

    finally:
        # Restore the original setting
        SystemSettings.AUTO_CREATE_FREE_SUBSCRIPTION = original_setting


@patch('services.email_service.EmailService.notify')
def test_create_free_subscription_when_enabled(mock_email_notify, client, db, create_test_auth_headers):
    """
    Test creating a free subscription when the system setting is enabled (default).
    """
    # Ensure free subscriptions are enabled (default)
    from config.system_settings import SystemSettings
    original_setting = SystemSettings.AUTO_CREATE_FREE_SUBSCRIPTION
    SystemSettings.AUTO_CREATE_FREE_SUBSCRIPTION = True
    
    try:
        # Create authenticated headers (this creates the user and returns auth headers)
        headers = create_test_auth_headers(db, "enabled_free_user@example.com", "devpass", RoleEnum.user)

        # Try to create a free subscription
        response = client.post(
            "/subscription/free",
            headers=headers
        )

        # Should succeed with 200 because free subscriptions are enabled
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["price_id"] == "free_plan"

    finally:
        # Restore the original setting
        SystemSettings.AUTO_CREATE_FREE_SUBSCRIPTION = original_setting