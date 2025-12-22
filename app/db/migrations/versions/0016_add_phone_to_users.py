"""Add phone column to users table

Revision ID: 0016_add_phone_to_users
Revises: 0015_update_test_passwords
Create Date: 2025-12-22

This migration adds a phone column to the users table to support
team member management with phone number field.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0016_add_phone_to_users"
down_revision = "0015_update_test_passwords"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add phone column to users table."""
    op.add_column(
        "users",
        sa.Column("phone", sa.String(20), nullable=True),
    )

    # Add index for phone lookups
    op.create_index("ix_users_phone", "users", ["phone"], unique=False)

    print("✅ Added 'phone' column to users table")


def downgrade() -> None:
    """Remove phone column from users table."""
    op.drop_index("ix_users_phone", table_name="users")
    op.drop_column("users", "phone")
