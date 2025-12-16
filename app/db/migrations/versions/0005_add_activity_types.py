"""Add job_published and team_member_updated to activity_type enum

Revision ID: 0005_add_activity_types
Revises: 0004_fix_sequence
Create Date: 2025-12-16

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0005_add_activity_types"
down_revision = "0004_fix_sequence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new values to activity_type ENUM
    # PostgreSQL allows adding values to ENUM with ALTER TYPE ... ADD VALUE
    op.execute("ALTER TYPE activity_type ADD VALUE IF NOT EXISTS 'job_published'")
    op.execute("ALTER TYPE activity_type ADD VALUE IF NOT EXISTS 'team_member_updated'")


def downgrade() -> None:
    # Note: PostgreSQL does not support removing values from ENUM easily
    # This would require recreating the type, which is complex
    # For simplicity, we leave this as a no-op
    pass
