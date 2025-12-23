"""Merge multiple heads

Revision ID: 0015
Revises: 0014, 0007_current_question_id
Create Date: 2025-12-23

This migration merges the two parallel branches:
- Main branch ending at 0014
- Interview branch ending at 0007_current_question_id
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0015"
down_revision = ("0014", "0007_current_question_id")  # Tuple for merge
branch_labels = None
depends_on = None


def upgrade() -> None:
    # This is a merge migration - no schema changes needed
    pass


def downgrade() -> None:
    # This is a merge migration - no schema changes needed
    pass
