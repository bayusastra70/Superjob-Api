"""Add training_type column to ojt_programs

Revision ID: 0057
Revises: 0056
Create Date: 2026-02-16

Menambahkan kolom training_type (onsite/remote/hybrid) ke tabel ojt_programs.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0057"
down_revision = "0056"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ojt_programs",
        sa.Column(
            "training_type",
            sa.String(20),
            nullable=True,
            server_default="onsite",
            comment="Format pelatihan: onsite, remote, hybrid",
        ),
    )
    # Index untuk filter
    op.create_index("ix_ojt_programs_training_type", "ojt_programs", ["training_type"])


def downgrade() -> None:
    op.drop_index("ix_ojt_programs_training_type", table_name="ojt_programs")
    op.drop_column("ojt_programs", "training_type")
