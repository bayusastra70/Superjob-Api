"""merge activity and candidate branches

Revision ID: d7908d5d838b
Revises: fc7f08e1fa99, a1b2c3d4e5f6, 4d5e6f7a8b9c
Create Date: 2025-12-10 19:36:05.011998

"""
from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

# revision identifiers, used by Alembic.
revision = "d7908d5d838b"
down_revision = ("fc7f08e1fa99", "a1b2c3d4e5f6", "4d5e6f7a8b9c")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Merge point; no-op.
    pass


def downgrade() -> None:
    # Merge point; no-op.
    pass
