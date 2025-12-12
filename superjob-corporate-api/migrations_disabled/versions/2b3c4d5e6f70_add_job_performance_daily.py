"""add job_performance_daily table"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2b3c4d5e6f70"
down_revision = "1a2b3c4d5e6f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_performance_daily",
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_title", sa.String(length=255), nullable=True),
        sa.Column("views_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("applicants_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("apply_rate", sa.Numeric(6, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.PrimaryKeyConstraint("job_id", "as_of_date"),
    )
    op.create_index(
        "ix_job_performance_daily_employer_date",
        "job_performance_daily",
        ["employer_id", "as_of_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_job_performance_daily_employer_date", table_name="job_performance_daily")
    op.drop_table("job_performance_daily")
