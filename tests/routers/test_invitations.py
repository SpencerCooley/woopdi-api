"""
Improved tests for invitation system using the new seed fixture.
These tests leverage the consistent test environment created by the seed fixture.
"""

import pytest
from unittest.mock import patch
from models import User, Organization, OrganizationUser, Invitation
from dependencies.dependencies import get_db
from dependencies.enums import RoleEnum
from types_definitions.invitation import InvitationCreate
from tests.conftest import get_user_auth_headers
import json
from types_definitions.organization_user import OrganizationUserRole

@patch('services.email_service.EmailService.notify')
def test_create_invitation_success_with_seed_fixture(mock_email_notify, client, db, seed_test_organizations_and_users):
    """
    Test that an invitation is created successfully by an organization admin.
    Uses the new seed fixture for consistent test environment.
    """
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    admin_user = seeded_data['user_subscribed']
    organization = seeded_data['organization']
    
    headers = get_user_auth_headers(db, admin_user)

    # Now create an invitation for a new user
    invitation_data = {
        "email": "invitee@example.com",
        "organization_id": organization.id
    }
    
    response = client.post(
        "/invitations",
        json=invitation_data,
        headers=headers
    )

    # Assert the API response is correct
    assert response.status_code == 201
    response_data = response.json()
    
    # Check that the response has the expected schema
    assert "email" in response_data
    assert "id" in response_data
    assert "organization_id" in response_data
    assert "inviter_id" in response_data
    assert "status" in response_data
    assert "expires_at" in response_data

    # Validate specific values
    assert response_data["email"] == "invitee@example.com"
    assert response_data["organization_id"] == organization.id
    assert response_data["inviter_id"] == admin_user.id
    assert response_data["status"] == "pending"
    
    # Verify that the invitation was actually stored in the database
    db_invitation = db.query(Invitation).filter(Invitation.email == "invitee@example.com").first()
    assert db_invitation is not None
    assert db_invitation.email == "invitee@example.com"
    assert db_invitation.organization_id == organization.id
    assert db_invitation.inviter_id == admin_user.id
    assert db_invitation.status == "pending"


@patch('services.email_service.EmailService.notify')
def test_create_invitation_to_org_user_is_not_member_of_fails(mock_email_notify, client, db, seed_test_organizations_and_users):
    """
    Test that creating an invitation fails for a user who is not a member of the target organization.
    Uses the new seed fixture for consistent test environment.
    """
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    admin_user = seeded_data['user_subscribed']
    organization = seeded_data['organization']
    organization2 = seeded_data['organization2']
    
    headers = get_user_auth_headers(db, admin_user)
    
    # Try to create an invitation to organization 2 (which admin user is not a member of)
    invitation_data = {
        "email": "invitee@example.com",
        "organization_id": organization2.id   # Trying to invite to organization2
    }
    
    response = client.post(
        "/invitations",
        json=invitation_data,
        headers=headers  # Using admin user's headers
    )
    
    # Should fail with 403 Forbidden because admin user is not a member of org2
    assert response.status_code == 403
    assert "sufficient privileges" in response.json()["detail"]

@patch('services.email_service.EmailService.notify')
def test_retrieve_invite_info_success(mock_email_notify, client, db, seed_test_organizations_and_users):
    """
    Test that we can get the invitation data after it has been created by using the token.
    Uses the new seed fixture for consistent test environment.
    """
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    admin_user = seeded_data['user_subscribed']
    organization = seeded_data['organization']
    
    headers = get_user_auth_headers(db, admin_user)
    
    # Create an invitation for the admin user
    invitation_data = {
        "email": "inviteeagain@example.com",
        "organization_id": organization.id
    }
    
    response = client.post(
        "/invitations",
        json=invitation_data,
        headers=headers
    )

    # Assert the API response is correct
    assert response.status_code == 201

    db_invitation = db.query(Invitation).filter(Invitation.email == "inviteeagain@example.com").first()
    invite_token = db_invitation.token

    the_url = f"/invitations/details?token={invite_token}"
    get_invite_data = client.get(the_url)
    
    assert get_invite_data.status_code == 200

def test_retrieve_invite_info_fail_with_wrong_token(client, db, create_test_auth_headers):
    """
    Tests that we don't retrive anything if we use a fake token. 
    """
    #user a completely made up token 
    invite_token = "completelymadeupfaketoken12345"

    the_url = f"/invitations/details?token={invite_token}"
    get_invite_data = client.get(the_url)
    
    # Should fail with 400 because the invitation is expired
    assert get_invite_data.status_code == 404
    response_data = get_invite_data.json()
    assert response_data["detail"] == "Invitation not found."

def test_retrieve_invite_info_fail_with_expired(client, db, seed_test_organizations_and_users):
    """
    Test that we get an error when trying to retrieve invitation data with an expired token.
    """
    from datetime import datetime, timedelta

    seeded_data = seed_test_organizations_and_users
    admin_user = seeded_data['user_subscribed']
    organization = seeded_data['organization']

    headers = get_user_auth_headers(db, admin_user)
    
    # Now create an invitation for the user (who will be the inviter)
    # We'll use a different email for the invitee
    invitation_data = {
        "email": "inviteeagain1@example.com",
        "organization_id": organization.id  # User's organization (non-solo)
    }
    
    response = client.post(
        "/invitations",
        json=invitation_data,
        headers=headers
    )
    
    # Assert the API response is correct
    assert response.status_code == 201
    
    # Get the invitation from the database
    db_invitation = db.query(Invitation).filter(Invitation.email == "inviteeagain1@example.com").first()
    invite_token = db_invitation.token
    
    # MODIFY THE INVITATION TO BE EXPIRED
    # Set expires_at to 8 days ago to make it expired
    expired_date = datetime.utcnow() - timedelta(days=8)
    db_invitation.expires_at = expired_date
    db.commit()  # Save the changes to the database
    
    # Now try to retrieve the invitation details with the expired token
    the_url = f"/invitations/details?token={invite_token}"
    get_invite_data = client.get(the_url)
    
    # Should fail with 400 because the invitation is expired
    assert get_invite_data.status_code == 400
    response_data = get_invite_data.json()
    assert response_data["detail"] == "Invitation has expired."



# testing the acceptance of an invitation 

# invitation must exist
@patch('services.email_service.EmailService.notify')
def test_invitation_accept_fails_if_invitation_does_not_exist(mock_email_notify, client):
    """
    test ensures that invite can not be accepted with a fake token not associated to an invite
    """
    accept_invite_data = {
        "token": "a_completely_made_up_token" # no password needed for this as it will fail before a passowrd is potentially needed. 
    }
    
    response = client.post(
        "/invitations/accept",
        json=accept_invite_data
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Invitation not found."

# ensure that the token invitation is not expired
@patch('services.email_service.EmailService.notify')
def test_inviation_accept_fails_if_invitation_is_expired(mock_email_notify, client, db, seed_test_organizations_and_users):
    """
    Test that we can not accept an invate that is expired. 
    """
    from datetime import datetime, timedelta
    
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    admin_user = seeded_data['user_subscribed']
    organization = seeded_data['organization']
    
    headers = get_user_auth_headers(db, admin_user)
    
    # Try to create a free subscription
    response = client.post(
        "/subscription/free",
        headers=headers
    )
    
    # Now create an invitation for the user (who will be the inviter)
    # We'll use a different email for the invitee
    invitation_data = {
        "email": "inviteeagain11@example.com",
        "organization_id": organization.id  # User's organization (non-solo)
    }
    
    response = client.post(
        "/invitations",
        json=invitation_data,
        headers=headers
    )
    
    # Assert the API response is correct
    assert response.status_code == 201
    
    # Get the invitation from the database
    db_invitation = db.query(Invitation).filter(Invitation.email == "inviteeagain11@example.com").first()
    invite_token = db_invitation.token
    
    # MODIFY THE INVITATION TO BE EXPIRED
    # Set expires_at to 8 days ago to make it expired
    expired_date = datetime.utcnow() - timedelta(days=8)
    db_invitation.expires_at = expired_date
    db.commit()  # Save the changes to the database
    
    #now finally try to accept the invitation, it should fail because we made the invite expired. 
    accept_invite_data = {
        "token": invite_token # no password needed for this as it will fail before a passowrd is potentially needed. 
    }
    
    response = client.post(
        "/invitations/accept",
        json=accept_invite_data
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invitation has expired."


# ensure that the token invitation has not alredy been accepted 
@patch('services.email_service.EmailService.notify')
def test_invitation_accept_fails_if_invitation_has_already_been_accepted(mock_email_notify, client, db, seed_test_organizations_and_users): 
    """
    Test that we can not accept an invate that has already been accepted
    """
    from datetime import datetime, timedelta
    
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    admin_user = seeded_data['user_subscribed']
    organization = seeded_data['organization']
    
    headers = get_user_auth_headers(db, admin_user)
    
    # Now create an invitation for the user (who will be the inviter)
    # We'll use a different email for the invitee
    invitation_data = {
        "email": "inviteeagain112@example.com",
        "organization_id": organization.id  # User's organization (non-solo)
    }
    
    response = client.post(
        "/invitations",
        json=invitation_data,
        headers=headers
    )
    
    # Assert the API response is correct
    assert response.status_code == 201

    # invitation is created, now we should change the status to accepted for the test 
    db_invitation = db.query(Invitation).filter(Invitation.email == "inviteeagain112@example.com").first()
    invite_token = db_invitation.token
    db_invitation.status = "accepted"
    db.commit()

    # now that the status is changed we attempt to accept the invite. It should fail. 
    accept_invite_data = {
        "token": invite_token # no password needed for this as it will fail before a passowrd is potentially needed. 
    }
    
    response = client.post(
        "/invitations/accept",
        json=accept_invite_data
    )

    assert response.status_code == 400
    
# ensure that a new user must provide a password to accept (the creation of their password because they are a new user)
@patch('services.email_service.EmailService.notify')
def test_invitation_accept_new_user_without_password_fails(mock_email_notify, client, db, seed_test_organizations_and_users):
    """
    Test that a brand new invited user must include a password to accept invitation.
    """
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    admin_user = seeded_data['user_subscribed']
    organization = seeded_data['organization']
    
    headers = get_user_auth_headers(db, admin_user)
    

    # Now create an invitation for the user (who will be the inviter)
    # We'll use a different email for the invitee
    invitation_data = {
        "email": "new_user@example.com",
        "organization_id": organization.id # User's organization (non-solo)
    }
    
    response = client.post(
        "/invitations",
        json=invitation_data,
        headers=headers
    )

    # Assert the API response is correct
    assert response.status_code == 201

    # Get the invitation from the database
    db_invitation = db.query(Invitation).filter(Invitation.email == "new_user@example.com").first()
    invite_token = db_invitation.token

    # Try to accept the invitation without providing a password
    accept_invite_data = {
        "token": invite_token
    }
    
    response = client.post(
        "/invitations/accept",
        json=accept_invite_data
    )

    # Should fail with 404 because user doesn't exist and password is required
    assert response.status_code == 404
    assert "A password is required to create a new account" in response.json()["detail"]

# ensures a new user is accepted when a password is provided
@patch('services.email_service.EmailService.notify')
def test_invitation_accept_new_user_with_password_success(mock_email_notify, client, db, seed_test_organizations_and_users):
    """
    Test that a brand new invited user successfully is added to an organization when a password is included.
    """
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    admin_user = seeded_data['user_subscribed']
    organization = seeded_data['organization']
    
    headers = get_user_auth_headers(db, admin_user)
    

    # Now create an invitation for the user (who will be the inviter)
    # We'll use a different email for the invitee
    invitation_data = {
        "email": "new_user2@example.com",
        "organization_id": organization.id  # User's organization (non-solo)
    }
    
    #send the invite
    response = client.post(
        "/invitations",
        json=invitation_data,
        headers=headers
    )

    # Assert the API response is correct
    assert response.status_code == 201

    # Get the invitation from the database
    db_invitation = db.query(Invitation).filter(Invitation.email == "new_user2@example.com").first()
    invite_token = db_invitation.token

    # Try to accept the invitation with a password
    accept_invite_data = {
        "token": invite_token,
        "password": "newuserpassword123"
    }
    
    response = client.post(
        "/invitations/accept",
        json=accept_invite_data
    )

    # Should succeed with 200 and return auth token
    assert response.status_code == 200
    response_data = response.json()
    assert "token" in response_data
    assert isinstance(response_data["token"], str)
    assert len(response_data["token"]) > 0

    # Verify the new user was created and added to the organization
    new_user = db.query(User).filter(User.email == "new_user2@example.com").first()
    assert new_user is not None
    assert new_user.email == "new_user2@example.com"
    
    # Verify the user is now part of the organization
    org_user = db.query(OrganizationUser).filter(
        OrganizationUser.user_id == new_user.id,
        OrganizationUser.organization_id == organization.id
    ).first()
    assert org_user is not None

# ensures an existing user is accepted without passord. 
@patch('services.email_service.EmailService.notify')
def test_invitation_accept_existing_user_success(mock_email_notify, client, db, seed_test_organizations_and_users):
    """
    Test that an existing invited user is added to an organization without using a password.
    """
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    admin_user = seeded_data['user_subscribed2']
    existing_user = seeded_data["member1"] # member 1 is not yet part of org2, but is part of org 1. They should not need to provide a password when accepting an invite from org 2. 
    organization = seeded_data['organization2'] # we will use org 2 with ADMIN2 and add an existing user that is not yet part of of org2
    
    headers = get_user_auth_headers(db, admin_user)


    # Create an invitation for the existing user to join the organization
    invitation_data = {
        "email": existing_user.email,
        "organization_id": organization.id  # Org 1
    }
    
    response = client.post(
        "/invitations",
        json=invitation_data,
        headers=headers # Using orge ADMIN headers
    )

    # Assert the API response is correct
    assert response.status_code == 201

    # Get the invitation from the database
    db_invitation = db.query(Invitation).filter(Invitation.email == existing_user.email).first()
    invite_token = db_invitation.token

    # Try to accept the invitation without password (since user already exists)
    accept_invite_data = {
        "token": invite_token
    }
    
    response = client.post(
        "/invitations/accept",
        json=accept_invite_data
    )

    # Should succeed with 200 and return success message (no auth token for existing users)
    assert response.status_code == 200
    response_data = response.json()
    assert "message" in response_data
    assert "Invitation accepted successfully" in response_data["message"]
    assert "You can now access the new organization" in response_data["message"]

    # Verify the existing user is now part of the organization
    org_user = db.query(OrganizationUser).filter(
        OrganizationUser.user_id == existing_user.id,
        OrganizationUser.organization_id == organization.id
    ).first()
    assert org_user is not None


@patch('services.email_service.EmailService.notify')
def test_moderator_can_invite_user_to_organization(mock_email_notify, client, db, seed_test_organizations_and_users):
    """
    Test that a moderator can invite a user to an organization.
    Uses the new seed fixture for consistent test environment.
    """
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    moderator_user = seeded_data['moderator_user']
    organization = seeded_data['organization']
    
    moderator_headers = get_user_auth_headers(db, moderator_user)
    
    # The moderator should be able to invite a new user
    response = client.post(
        "/invitations",
        json={
            "email": "invited@example.com",
            "organization_id": organization.id
        },
        headers=moderator_headers
    )
    
    # Should succeed with 201
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["email"] == "invited@example.com"
    
    # Verify the invitation was created
    invitation = db.query(Invitation).filter(Invitation.email == "invited@example.com").first()
    assert invitation is not None
    assert invitation.organization_id == organization.id
    assert invitation.inviter_id == moderator_user.id  # The moderator invited



    """
    Test that a brand new invited user successfully is added to an organization when a password is included.
    Uses the new seed fixture for consistent test environment.
    """
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    admin_user = seeded_data['user_subscribed']
    organization = seeded_data['organization']

    headers = get_user_auth_headers(db, admin_user)
    
    # Create an invitation for a new user
    invitation_data = {
        "email": "new_user2@example.com",
        "organization_id": organization.id
    }
    
    response = client.post(
        "/invitations",
        json=invitation_data,
        headers=headers
    )

    # Assert the API response is correct
    assert response.status_code == 201

    # Get the invitation from the database
    db_invitation = db.query(Invitation).filter(Invitation.email == "new_user2@example.com").first()
    invite_token = db_invitation.token

    # Try to accept the invitation with a password
    accept_invite_data = {
        "token": invite_token,
        "password": "newuserpassword123"
    }
    
    response = client.post(
        "/invitations/accept",
        json=accept_invite_data
    )

    # Should succeed with 200 and return auth token
    assert response.status_code == 200
    response_data = response.json()
    assert "token" in response_data
    assert isinstance(response_data["token"], str)
    assert len(response_data["token"]) > 0

    # Verify the new user was created and added to the organization
    new_user = db.query(User).filter(User.email == "new_user2@example.com").first()
    assert new_user is not None
    assert new_user.email == "new_user2@example.com"
    
    # Verify the user is now part of the organization
    org_user = db.query(OrganizationUser).filter(
        OrganizationUser.user_id == new_user.id,
        OrganizationUser.organization_id == organization.id
    ).first()
    assert org_user is not None