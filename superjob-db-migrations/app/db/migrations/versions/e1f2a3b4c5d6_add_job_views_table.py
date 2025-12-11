"""add job_views table for job performance aggregates

Revision ID: e1f2a3b4c5d6
Revises: d7908d5d838b
Create Date: 2025-12-11 13:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e1f2a3b4c5d6"
down_revision = "d7908d5d838b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_views",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("viewed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_job_views_job_id", "job_views", ["job_id"])
    op.create_index("ix_job_views_viewed_at", "job_views", ["viewed_at"])


def downgrade() -> None:
    op.drop_index("ix_job_views_viewed_at", table_name="job_views")
    op.drop_index("ix_job_views_job_id", table_name="job_views")
    op.drop_table("job_views")
