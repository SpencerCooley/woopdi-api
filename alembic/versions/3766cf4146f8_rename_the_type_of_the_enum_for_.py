"""rename the type of the enum for consistency in type management
Revision ID: 3766cf4146f8
Revises: 5e66cffecae8
Create Date: 2025-08-29 23:47:49.695146
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3766cf4146f8'
down_revision = '5e66cffecae8'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Step 1: Create the new enum type
    op.execute("CREATE TYPE organizationuserrole AS ENUM ('ADMIN', 'MODERATOR', 'MEMBER')")
    
    # Step 2: Change the column to use the new enum type
    op.execute("""
        ALTER TABLE organization_users 
        ALTER COLUMN role TYPE organizationuserrole 
        USING role::text::organizationuserrole
    """)
    
    # Step 3: Drop the old enum type
    op.execute("DROP TYPE organizationrole")

def downgrade() -> None:
    # Step 1: Create the old enum type
    op.execute("CREATE TYPE organizationrole AS ENUM ('ADMIN', 'MEMBER', 'MODERATOR')")
    
    # Step 2: Change the column back to use the old enum type
    op.execute("""
        ALTER TABLE organization_users 
        ALTER COLUMN role TYPE organizationrole 
        USING role::text::organizationrole
    """)
    
    # Step 3: Drop the new enum type
    op.execute("DROP TYPE organizationuserrole")