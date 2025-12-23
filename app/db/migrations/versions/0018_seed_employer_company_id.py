"""Update employer users with company_id

Revision ID: 0018_seed_employer_company_id
Revises: 0017_add_company_fk_to_users
Create Date: 2025-12-23

This migration updates existing employer users with their associated company_id.
- employer@superjob.com (id=8) -> PT SuperJob Indonesia (id=1)
- tanaka@gmail.com (id=3) -> TechCorp Solutions (id=2)
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0018_seed_employer_company_id"
down_revision = "0017_add_company_fk_to_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update employer users with their company_id."""

    # Update employer@superjob.com (id=8) with company_id=1 (PT SuperJob Indonesia)
    op.execute("""
        UPDATE users 
        SET company_id = 1, updated_at = CURRENT_TIMESTAMP
        WHERE id = 8 AND email = 'employer@superjob.com'
    """)

    # Update tanaka@gmail.com (id=3) with company_id=2 (TechCorp Solutions)
    op.execute("""
        UPDATE users 
        SET company_id = 2, updated_at = CURRENT_TIMESTAMP
        WHERE id = 3 AND email = 'tanaka@gmail.com'
    """)

    print("✅ Updated employer users with company_id:")
    print("   - employer@superjob.com (id=8) -> company_id=1 (PT SuperJob Indonesia)")
    print("   - tanaka@gmail.com (id=3) -> company_id=2 (TechCorp Solutions)")


def downgrade() -> None:
    """Remove company_id from employer users."""
    op.execute("""
        UPDATE users 
        SET company_id = NULL, updated_at = CURRENT_TIMESTAMP
        WHERE id IN (8, 3)
    """)
