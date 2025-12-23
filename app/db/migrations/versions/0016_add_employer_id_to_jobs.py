"""Add employer_id column to jobs table

Revision ID: 0016
Revises: 0015
Create Date: 2025-12-23

This migration adds the missing employer_id column to the jobs table.
The column was expected by the Job model but was missing from the database.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add employer_id column
    # First add as nullable to avoid issues with existing rows
    op.add_column("jobs", sa.Column("employer_id", sa.Integer(), nullable=True))

    # Populate employer_id from created_by for existing jobs
    op.execute("""
        UPDATE jobs 
        SET employer_id = created_by 
        WHERE employer_id IS NULL AND created_by IS NOT NULL
    """)

    # For any remaining rows without employer_id, set a default
    # or you can make it nullable - here we keep it nullable for safety

    # Create index
    op.create_index("ix_jobs_employer_id", "jobs", ["employer_id"])

    # Add foreign key constraint
    op.create_foreign_key(
        "fk_jobs_employer_id_users",
        "jobs",
        "users",
        ["employer_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_jobs_employer_id_users", "jobs", type_="foreignkey")
    op.drop_index("ix_jobs_employer_id", table_name="jobs")
    op.drop_column("jobs", "employer_id")
