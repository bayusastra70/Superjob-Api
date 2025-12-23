"""Add company_id foreign key to users table

Revision ID: 0017_add_company_fk_to_users
Revises: 0016_add_phone_to_users
Create Date: 2025-12-23

This migration adds a company_id column to users table with a proper
foreign key relationship to the companies table. This allows employers
to be associated with a company, and when creating jobs, the system
will automatically populate company_id from the employer's record.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0017_add_company_fk_to_users"
down_revision = "0016_add_phone_to_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add company_id column with FK to users table."""
    # Check if column already exists
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = [col["name"] for col in inspector.get_columns("users")]

    if "company_id" not in columns:
        # Add company_id column (BigInteger to match companies.id type)
        op.add_column(
            "users",
            sa.Column("company_id", sa.BigInteger(), nullable=True),
        )
        print("✅ Added 'company_id' column to users table")
    else:
        print("ℹ️ 'company_id' column already exists in users table, skipping...")

    # Check if index already exists before creating
    indexes = [idx["name"] for idx in inspector.get_indexes("users")]
    if "ix_users_company_id" not in indexes:
        op.create_index("ix_users_company_id", "users", ["company_id"], unique=False)
        print("✅ Created index 'ix_users_company_id'")
    else:
        print("ℹ️ Index 'ix_users_company_id' already exists, skipping...")

    # Note: FK constraint removed because companies.id doesn't have PRIMARY KEY constraint
    # The relationship between users.company_id and companies.id is maintained at application level
    print("ℹ️ FK constraint skipped (companies.id has no PRIMARY KEY constraint)")


def downgrade() -> None:
    """Remove company_id column from users table."""
    # Note: No FK constraint to drop since we didn't create one
    op.drop_index("ix_users_company_id", table_name="users")
    op.drop_column("users", "company_id")
