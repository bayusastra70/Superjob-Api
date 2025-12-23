"""Add more activity types to enum

Revision ID: 0006
Revises: 0005
Create Date: 2024-12-17
"""

from alembic import op

revision = "0006"
down_revision = "0005_add_activity_types"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new values to activity_type ENUM
    op.execute("ALTER TYPE activity_type ADD VALUE IF NOT EXISTS 'job_status_changed'")
    op.execute(
        "ALTER TYPE activity_type ADD VALUE IF NOT EXISTS 'company_profile_updated'"
    )
    op.execute("ALTER TYPE activity_type ADD VALUE IF NOT EXISTS 'candidate_uploaded'")


def downgrade() -> None:
    # PostgreSQL tidak mendukung DROP VALUE dari ENUM
    # Perlu recreate type jika ingin rollback
    pass
