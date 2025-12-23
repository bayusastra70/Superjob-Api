"""Add scam detection fields to jobs table

Revision ID: 0014
Revises: 0013
Create Date: 2025-01-XX
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("jobs") as batch:
        # Flag utama
        batch.add_column(
            sa.Column(
                "is_scam",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            )
        )

        # Nilai skor 0.0 – 1.0
        batch.add_column(
            sa.Column(
                "scam_score",
                sa.Float(),
                nullable=True,
            )
        )

        # Detail sinyal (list of dict)
        batch.add_column(
            sa.Column(
                "scam_signals",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=True,
            )
        )

        # Tags hasil analisis (mis: scam, pay-to-apply, whatsapp-only)
        batch.add_column(
            sa.Column(
                "tags",
                postgresql.ARRAY(sa.Text()),
                nullable=False,
                server_default=sa.text("ARRAY[]::text[]"),
            )
        )

    # Index untuk query & filtering
    op.create_index("idx_jobs_is_scam", "jobs", ["is_scam"], unique=False)
    op.create_index("idx_jobs_status_is_scam", "jobs", ["status", "is_scam"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_jobs_status_is_scam", table_name="jobs")
    op.drop_index("idx_jobs_is_scam", table_name="jobs")

    with op.batch_alter_table("jobs") as batch:
        batch.drop_column("tags")
        batch.drop_column("scam_signals")
        batch.drop_column("scam_score")
        batch.drop_column("is_scam")
