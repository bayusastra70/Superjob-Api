"""Add company relation and salary fields to jobs table

Revision ID: 0010
Revises: 0009
Create Date: 2025-01-15
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade():
    # ============================
    # ADD NEW COLUMNS
    # ============================

    op.add_column(
        "jobs",
        sa.Column("company_id", sa.BigInteger(), nullable=True),
    )

    op.add_column(
        "jobs",
        sa.Column("salary_min", sa.Numeric(12, 2), nullable=True),
    )

    op.add_column(
        "jobs",
        sa.Column("salary_max", sa.Numeric(12, 2), nullable=True),
    )

    op.add_column(
        "jobs",
        sa.Column("salary_currency", sa.String(length=8), nullable=True),
    )

    op.add_column(
        "jobs",
        sa.Column("benefits", sa.Text(), nullable=True),
    )

    op.add_column(
        "jobs",
        sa.Column("contact_url", sa.String(length=512), nullable=True),
    )

    # ============================
    # INDEXES
    # ============================

    op.create_index(
        "ix_jobs_company_id",
        "jobs",
        ["company_id"],
        unique=False,
    )


def downgrade():
    # ============================
    # DROP FOREIGN KEY
    # ============================

    # ============================
    # DROP INDEX
    # ============================

    op.drop_index("ix_jobs_company_id", table_name="jobs")

    # ============================
    # DROP COLUMNS
    # ============================

   
    op.drop_column("jobs", "contact_url")
    op.drop_column("jobs", "benefits")
    op.drop_column("jobs", "salary_currency")
    op.drop_column("jobs", "salary_max")
    op.drop_column("jobs", "salary_min")
    op.drop_column("jobs", "company_id")
