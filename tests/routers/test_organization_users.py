# test getting a list of user in an organization
from tests.conftest import get_user_auth_headers
from fastapi import status
from types_definitions.organization_user import OrganizationUserRole

# a moderator can get the org user list
def test_moderator_can_get_user_list(client, db, seed_test_organizations_and_users):
    # need to create a situation where there is an organization with multiple 
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    moderator_user = seeded_data['moderator_user']
    organization = seeded_data['organization']
    
    headers = get_user_auth_headers(db, moderator_user)

    response = client.get(
        f"/organization-users/{organization.id}",
        headers=headers
    )

    assert response.status_code == 200
    assert len(response.json()) > 1  

# an admin can get the org user list
def test_admin_can_get_user_list(client, db, seed_test_organizations_and_users):
    # need to create a situation where there is an organization with multiple 
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    admin_user = seeded_data['user_subscribed']
    organization = seeded_data['organization']
    
    headers = get_user_auth_headers(db, admin_user)

    response = client.get(
        f"/organization-users/{organization.id}",
        headers=headers
    )

    assert response.status_code == 200
    assert len(response.json()) > 1  


# a member can not get the list of users that are part of the organization
def test_member_can_not_get_user_list(client, db, seed_test_organizations_and_users):
    # need to create a situation where there is an organization with multiple 
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    member_user = seeded_data['member1']
    organization = seeded_data['organization']
    
    headers = get_user_auth_headers(db, member_user)

    response = client.get(
        f"/organization-users/{organization.id}",
        headers=headers
    )

    assert response.status_code == 403


# role change tests /organization-users/{org_id}/{user_id}

# test that a MODERATOR can NOT change the role of an ADMIN 
def test_moderator_cannot_change_admin_role(client, db, seed_test_organizations_and_users):
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    moderator_user = seeded_data['moderator_user']
    organization = seeded_data['organization']
    admin_user = seeded_data['user_subscribed']
    
    headers = get_user_auth_headers(db, moderator_user)
    
    # Try to change the role of an ADMIN user to MODERATOR
    response = client.put(
        f"/organization-users/{organization.id}/{admin_user.id}",
        json={"role": "MODERATOR"},
        headers=headers
    )
    
    assert response.status_code == 403
    assert "Moderators can only modify users with MEMBER role" in response.json()["detail"]

# test that a MODERATOR can NOT change the role of another MODERATOR
def test_moderator_cannot_change_moderator_role(client, db, seed_test_organizations_and_users):
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    moderator_user = seeded_data['moderator_user']
    organization = seeded_data['organization']
    another_moderator = seeded_data['moderator_user']  # Same user for simplicity
    
    headers = get_user_auth_headers(db, moderator_user)
    
    # Try to change the role of another MODERATOR user to MEMBER
    response = client.put(
        f"/organization-users/{organization.id}/{another_moderator.id}",
        json={"role": "MEMBER"},
        headers=headers
    )
    
    assert response.status_code == 403
    assert "Moderators can only modify users with MEMBER role" in response.json()["detail"]

# test that a MODERATOR CAN change the role of a MEMBER
def test_moderator_can_change_member_role(client, db, seed_test_organizations_and_users):
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    moderator_user = seeded_data['moderator_user']
    organization = seeded_data['organization']
    member_user = seeded_data['member3']
    
    headers = get_user_auth_headers(db, moderator_user)
    
    # Change a MEMBER user to MODERATOR
    response = client.put(
        f"/organization-users/{organization.id}/{member_user.id}",
        json={"role": "MODERATOR"},
        headers=headers
    )
    print(response.json())
    print(response.json())
    print(response.json())
    print(response.json())
    print(response.json())
    print(response.json())
    print(response.json())
    print(response.json())
    print(response.json())
    assert response.status_code == 200
    
    assert response.json()["role"] == "MODERATOR"

# test that a MEMBER can NOT change the role of anyone
def test_member_cannot_change_anyone_role(client, db, seed_test_organizations_and_users):
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    member_user = seeded_data['member1']
    organization = seeded_data['organization']
    another_member = seeded_data['member2']
    
    headers = get_user_auth_headers(db, member_user)
    
    # Try to change the role of another user
    response = client.put(
        f"/organization-users/{organization.id}/{another_member.id}",
        json={"role": "MODERATOR"},
        headers=headers
    )
    
    assert response.status_code == 403
    assert "do not have sufficient privileges" in response.json()["detail"]


# remove member tests /organization-users/{org_id}/{user_id}

# test that a MODERATOR can NOT remove a user with the role of ADMIN
def test_moderator_cannot_remove_admin(client, db, seed_test_organizations_and_users):
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    moderator_user = seeded_data['moderator_user']
    organization = seeded_data['organization']
    admin_user = seeded_data['user_subscribed']
    
    headers = get_user_auth_headers(db, moderator_user)
    
    # Try to remove an ADMIN user
    response = client.delete(
        f"/organization-users/{organization.id}/{admin_user.id}",
        headers=headers
    )
    
    assert response.status_code == 403
    assert "Moderators can only delete users with MEMBER role" in response.json()["detail"]

# test that a MODERATOR can NOT remove a user with the role of MODERATOR 
def test_moderator_cannot_remove_moderator(client, db, seed_test_organizations_and_users):
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    moderator_user = seeded_data['moderator_user']
    organization = seeded_data['organization']
    another_moderator = seeded_data['moderator_user']  # Same user for simplicity
    
    headers = get_user_auth_headers(db, moderator_user)
    
    # Try to remove another MODERATOR user
    response = client.delete(
        f"/organization-users/{organization.id}/{another_moderator.id}",
        headers=headers
    )
    
    assert response.status_code == 403
    assert "Moderators can only delete users with MEMBER role" in response.json()["detail"]

# test that a MODERATOR CAN remove a MEMBER. 
def test_moderator_can_remove_member(client, db, seed_test_organizations_and_users):
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    moderator_user = seeded_data['moderator_user']
    organization = seeded_data['organization']
    member_user = seeded_data['member1']
    
    headers = get_user_auth_headers(db, moderator_user)
    
    # Remove a MEMBER user
    response = client.delete(
        f"/organization-users/{organization.id}/{member_user.id}",
        headers=headers
    )
    
    assert response.status_code == 200
    assert "removed from organization" in response.json()["message"]

# test that an admin can remove anyone from the organization. 
def test_admin_can_remove_anyone(client, db, seed_test_organizations_and_users):
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    admin_user = seeded_data['user_subscribed']
    organization = seeded_data['organization']
    member_user = seeded_data['member1']
    moderator_user = seeded_data['moderator_user']
    member2_user = seeded_data['member2']  # Another member to test role change
    
    headers = get_user_auth_headers(db, admin_user)
    
    # Remove a MEMBER user
    response = client.delete(
        f"/organization-users/{organization.id}/{member_user.id}",
        headers=headers
    )
    
    assert response.status_code == 200
    assert "removed from organization" in response.json()["message"]
    
    # Remove a MODERATOR user
    response = client.delete(
        f"/organization-users/{organization.id}/{moderator_user.id}",
        headers=headers
    )
    
    assert response.status_code == 200
    assert "removed from organization" in response.json()["message"]
    
    # Test that admin can change a member to admin and then remove them
    # First, change member2 to be an admin
    response = client.put(
        f"/organization-users/{organization.id}/{member2_user.id}",
        json={"role": "ADMIN"},
        headers=headers
    )
    
    assert response.status_code == 200
    assert response.json()["role"] == "ADMIN"
    
    # Then remove the admin (member2)
    response = client.delete(
        f"/organization-users/{organization.id}/{member2_user.id}",
        headers=headers
    )
    
    assert response.status_code == 200
    assert "removed from organization" in response.json()["message"]

# test that an admin can NOT remove themself. 
def test_admin_cannot_remove_themselves(client, db, seed_test_organizations_and_users):
    # Get the seeded data
    seeded_data = seed_test_organizations_and_users
    admin_user = seeded_data['user_subscribed']
    organization = seeded_data['organization']
    
    headers = get_user_auth_headers(db, admin_user)
    
    # Try to remove self
    response = client.delete(
        f"/organization-users/{organization.id}/{admin_user.id}",
        headers=headers
    )
    
    assert response.status_code == 400
    assert "You cannot delete yourself from the organization" in response.json()["detail"]