"""Remove employer_id column from jobs table

Revision ID: 0018_remove_employer_id_only
Revises: 0017_remove_job_postings_table
Create Date: 2025-12-23

This migration:
1. Removes employer_id column from jobs table
   (created_by is used instead)
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0018'
down_revision = '0017'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========== STEP 1: Drop foreign key for employer_id ==========
    try:
        op.drop_constraint(
            'fk_jobs_employer_id_users',
            'jobs',
            type_='foreignkey'
        )
    except Exception:
        pass

    # ========== STEP 2: Drop index for employer_id ==========
    try:
        op.drop_index('ix_jobs_employer_id', table_name='jobs')
    except Exception:
        pass

    # ========== STEP 3: Drop employer_id column ==========
    op.drop_column('jobs', 'employer_id')

    print("Note: jobs.created_by is now the single source of job ownership")


def downgrade() -> None:
    # ========== STEP 1: Re-add employer_id column ==========
    op.add_column(
        'jobs',
        sa.Column('employer_id', sa.Integer(), nullable=True)
    )

    # ========== STEP 2: Restore employer_id from created_by ==========
    op.execute("""
        UPDATE jobs
        SET employer_id = created_by
        WHERE employer_id IS NULL
    """)

    # ========== STEP 3: Recreate foreign key ==========
    op.create_foreign_key(
        'fk_jobs_employer_id_users',
        'jobs',
        'users',
        ['employer_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # ========== STEP 4: Recreate index ==========
    op.create_index('ix_jobs_employer_id', 'jobs', ['employer_id'])
