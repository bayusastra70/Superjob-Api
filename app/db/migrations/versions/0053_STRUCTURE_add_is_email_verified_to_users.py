"""Add is_email_verified column to users table

Revision ID: 0053
Revises: 0052
Create Date: 2025-02-05
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0053"
down_revision = "0052"
branch_labels = None
depends_on = None


def upgrade():
    # Add is_email_verified column to users table
    op.add_column(
        "users",
        sa.Column(
            "is_email_verified", sa.Boolean(), nullable=False, server_default="false"
        ),
    )

    # Create index for faster lookups
    op.create_index(
        "ix_users_is_email_verified", "users", ["is_email_verified"], unique=False
    )

    # Update existing users who are already active to have is_email_verified = true
    # This ensures backward compatibility - existing active users are considered verified
    op.execute("""
        UPDATE users 
        SET is_email_verified = true 
        WHERE is_active = true
    """)


def downgrade():
    # Drop index first
    op.drop_index("ix_users_is_email_verified", table_name="users")

    # Drop column
    op.drop_column("users", "is_email_verified")
