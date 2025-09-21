"""
Organization and Subscription seeding functions.
"""

import os
import sys
from sqlalchemy.orm import Session
from passlib.context import CryptContext

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import User
from models.organization import Organization, OrganizationUser, Subscription
from dependencies.enums import RoleEnum
from types_definitions.organization_user import OrganizationUserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_organizations_and_subscriptions(session: Session):
    """
    Creates organizations and subscriptions for the default users.
    """
    users_data = [
        {'email': 'super@admin.com', 'role': RoleEnum.superadmin},
        {'email': 'admin@admin.com', 'role': RoleEnum.admin},
        {'email': 'customer@customer.com', 'role': RoleEnum.user},
        {'email': 'user@user.com', 'role': RoleEnum.user},
        {'email': 'user_subscribed@user.com', 'role': RoleEnum.user},
        {'email': 'moderator@usersubscribed.com', 'role': RoleEnum.user},
        {'email': 'user_subscribed2@user.com', 'role': RoleEnum.user}, # the second organization owner
        {'email': 'member1@usersubscribed.com', 'role': RoleEnum.user},
        {'email': 'member2@usersubscribed.com', 'role': RoleEnum.user},
        {'email': 'member3@usersubscribed.com', 'role': RoleEnum.user}, # should also belong to the user_subscribed2 org
        {'email': 'member4@usersubscribed.com', 'role': RoleEnum.user}, # should also belong to the user_subscribed2 org
    ]

    # Create users if they don't exist
    hashed_password = pwd_context.hash("devpass")
    for user_data in users_data:
        user = session.query(User).filter(User.email == user_data['email']).first()
        if not user:
            user = User(email=user_data['email'], hashed_password=hashed_password, role=user_data['role'], confirmed=True)
            session.add(user)
    session.commit()

    # Create solo organizations for all users
    for user_data in users_data:
        user = session.query(User).filter(User.email == user_data['email']).first()
        if not session.query(Organization).join(OrganizationUser).filter(OrganizationUser.user_id == user.id, Organization.is_solo == True).first():
            solo_org = Organization(name=f"{user.email}'s solo org", is_solo=True, org_owner=user.id)
            session.add(solo_org)
            session.flush()
            org_user = OrganizationUser(user_id=user.id, organization_id=solo_org.id, role=OrganizationUserRole.ADMIN)
            session.add(org_user)
            print(f"Created solo organization for {user.email}")

    # Create non-solo organization and subscription for user_subscribed@user.com
    subscribed_user = session.query(User).filter(User.email == 'user_subscribed@user.com').first()
    if not session.query(Organization).join(OrganizationUser).filter(OrganizationUser.user_id == subscribed_user.id, Organization.is_solo == False).first():
        non_solo_org = Organization(name="Subscribed Org", is_solo=False, org_owner=subscribed_user.id)
        session.add(non_solo_org)
        session.flush()
        org_user = OrganizationUser(user_id=subscribed_user.id, organization_id=non_solo_org.id, role=OrganizationUserRole.ADMIN)
        session.add(org_user)
        print(f"Created non-solo organization for {subscribed_user.email}")

        # Add subscription
        subscription = Subscription(
            organization_id=non_solo_org.id,
            stripe_subscription_id="sub_placeholder_123",
            status="active",
            price_id="price_placeholder_123"
        )
        session.add(subscription)
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
            member = session.query(User).filter(User.email == email).first()
            role = OrganizationUserRole.MODERATOR if email == 'moderator@usersubscribed.com' else OrganizationUserRole.MEMBER
            org_user = OrganizationUser(user_id=member.id, organization_id=non_solo_org.id, role=role)
            session.add(org_user)
            print(f"Added {email} to Subscribed Org with role {role.value}")


    # Create non-solo organization and subscription for user_subscribed2@user.com
    subscribed_user = session.query(User).filter(User.email == 'user_subscribed2@user.com').first()
    if not session.query(Organization).join(OrganizationUser).filter(OrganizationUser.user_id == subscribed_user.id, Organization.is_solo == False).first():
        non_solo_org = Organization(name="Subscribed Org 2", is_solo=False, org_owner=subscribed_user.id)
        session.add(non_solo_org)
        session.flush()
        org_user = OrganizationUser(user_id=subscribed_user.id, organization_id=non_solo_org.id, role=OrganizationUserRole.ADMIN)
        session.add(org_user)
        print(f"Created non-solo organization for {subscribed_user.email}")

        # Add subscription
        subscription = Subscription(
            organization_id=non_solo_org.id,
            stripe_subscription_id="sub_placeholder_1243",
            status="active",
            price_id="price_placeholder_123"
        )
        session.add(subscription)
        print(f"Created subscription for {subscribed_user.email}")

        # Add members to the non-solo organization
        member_emails = [
            'member3@usersubscribed.com',
            'member4@usersubscribed.com'
        ]
        for email in member_emails:
            member = session.query(User).filter(User.email == email).first()
            org_user = OrganizationUser(user_id=member.id, organization_id=non_solo_org.id, role=OrganizationUserRole.MEMBER)
            session.add(org_user)
            print(f"Added {email} to Subscribed Org")

    session.commit()
