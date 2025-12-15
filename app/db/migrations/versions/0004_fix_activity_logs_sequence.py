"""Fix activity_logs sequence to avoid duplicate key errors.

Revision ID: 0004_fix_sequence
Revises: 0003_cleanup_role_redundancy
Create Date: 2025-12-15
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0004_fix_sequence"
down_revision = "0003_cleanup_role_redundancy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Reset the activity_logs id sequence to MAX(id) + 1
    # This prevents duplicate key errors when inserting new rows
    op.execute("""
        SELECT setval(
            pg_get_serial_sequence('activity_logs', 'id'),
            COALESCE((SELECT MAX(id) FROM activity_logs), 0) + 1,
            false
        );
    """)


def downgrade() -> None:
    # No action needed for downgrade
    pass
