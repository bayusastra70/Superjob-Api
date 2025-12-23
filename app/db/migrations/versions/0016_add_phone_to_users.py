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
    # Check if column already exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col["name"] for col in inspector.get_columns("users")]

    if "phone" not in columns:
        op.add_column(
            "users",
            sa.Column("phone", sa.String(20), nullable=True),
        )
        print("✅ Added 'phone' column to users table")
    else:
        print("ℹ️ 'phone' column already exists in users table, skipping...")

    # Check if index already exists before creating
    indexes = [idx["name"] for idx in inspector.get_indexes("users")]
    if "ix_users_phone" not in indexes:
        op.create_index("ix_users_phone", "users", ["phone"], unique=False)
        print("✅ Created index 'ix_users_phone'")
    else:
        print("ℹ️ Index 'ix_users_phone' already exists, skipping...")


def downgrade() -> None:
    """Remove phone column from users table."""
    op.drop_index("ix_users_phone", table_name="users")
    op.drop_column("users", "phone")
