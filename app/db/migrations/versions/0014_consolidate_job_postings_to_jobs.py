"""Consolidate job_postings table into jobs table

This migration:
1. Adds missing columns to jobs table (employer_id, skills, education, etc.)
2. Migrates data from job_postings to jobs
3. Updates foreign key in reminder_tasks from job_postings to jobs
4. Drops job_postings table

Revision ID: 0014
Revises: 0013
Create Date: 2024-12-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Consolidate job_postings into jobs table.
    This removes redundancy between the two tables.
    """

    # ========================================
    # STEP 1: Add missing columns to jobs table
    # ========================================

    # employer_id - who posted the job
    op.add_column(
        "jobs",
        sa.Column("employer_id", sa.Integer(), nullable=True),
    )

    # skills - JSON array of skills
    op.add_column(
        "jobs",
        sa.Column("skills", JSON, nullable=True),
    )

    # education - education requirement
    op.add_column(
        "jobs",
        sa.Column("education", sa.String(100), nullable=True),
    )

    # Create index for employer_id
    op.create_index(
        "ix_jobs_employer_id",
        "jobs",
        ["employer_id"],
        unique=False,
    )

    # ========================================
    # STEP 1.5: Make job_code nullable (data from job_postings has no job_code)
    # ========================================

    # Drop UNIQUE constraint on job_code first
    op.drop_constraint("jobs_job_code_key", "jobs", type_="unique")

    # Alter job_code to be nullable
    op.alter_column(
        "jobs",
        "job_code",
        existing_type=sa.String(50),
        nullable=True,
    )

    # ========================================
    # STEP 2: Create FK constraint for employer_id
    # ========================================
    op.create_foreign_key(
        "fk_jobs_employer_id",
        "jobs",
        "users",
        ["employer_id"],
        ["id"],
    )

    # ========================================
    # STEP 3: Migrate data from job_postings to jobs WITH MAPPING
    # ========================================

    # Create temporary mapping table to preserve UUID -> Integer relationship
    op.execute("""
        CREATE TEMPORARY TABLE job_id_mapping (
            old_uuid VARCHAR(36) PRIMARY KEY,
            new_int_id INTEGER
        )
    """)

    # First, get all job_postings with their UUIDs and assign row numbers
    # Then insert to jobs and use row numbers to match back
    op.execute("""
        WITH numbered_postings AS (
            SELECT 
                id as old_uuid,
                employer_id,
                title,
                description,
                salary_min,
                salary_max,
                salary_currency,
                skills,
                location,
                employment_type,
                experience_level,
                education,
                benefits,
                contact_url,
                status::text as status,
                created_at,
                updated_at,
                ROW_NUMBER() OVER (ORDER BY created_at, id) as rn
            FROM job_postings
        ),
        inserted_jobs AS (
            INSERT INTO jobs (
                employer_id, title, description, salary_min, salary_max,
                salary_currency, skills, location, employment_type,
                experience_level, education, benefits, contact_url,
                status, created_at, updated_at
            )
            SELECT 
                employer_id, title, description, salary_min, salary_max,
                salary_currency, skills, location, employment_type,
                experience_level, education, benefits, contact_url,
                status, created_at, updated_at
            FROM numbered_postings
            ORDER BY rn
            RETURNING id
        ),
        numbered_inserted AS (
            SELECT id as new_int_id, ROW_NUMBER() OVER (ORDER BY id) as rn
            FROM inserted_jobs
        )
        INSERT INTO job_id_mapping (old_uuid, new_int_id)
        SELECT np.old_uuid, ni.new_int_id
        FROM numbered_postings np
        INNER JOIN numbered_inserted ni ON np.rn = ni.rn
    """)

    # ========================================
    # STEP 4: Update reminder_tasks foreign key
    # ========================================

    # Drop old FK constraint from job_postings
    op.drop_constraint(
        "reminder_tasks_job_id_fkey", "reminder_tasks", type_="foreignkey"
    )

    # First, add a temporary column to store the new Integer job_id
    op.add_column(
        "reminder_tasks",
        sa.Column("job_id_new", sa.Integer(), nullable=True),
    )

    # Update the new column using the mapping table
    op.execute("""
        UPDATE reminder_tasks rt
        SET job_id_new = m.new_int_id
        FROM job_id_mapping m
        WHERE rt.job_id = m.old_uuid
    """)

    # Drop the old job_id column (String/UUID)
    op.drop_column("reminder_tasks", "job_id")

    # Rename the new column to job_id
    op.alter_column(
        "reminder_tasks",
        "job_id_new",
        new_column_name="job_id",
    )

    # Create new FK constraint to jobs table
    op.create_foreign_key(
        "fk_reminder_tasks_job_id",
        "reminder_tasks",
        "jobs",
        ["job_id"],
        ["id"],
    )

    # Drop the temporary mapping table (it will be dropped automatically at end of transaction,
    # but let's be explicit)
    op.execute("DROP TABLE IF EXISTS job_id_mapping")

    # ========================================
    # STEP 5: Drop job_postings table
    # ========================================

    # Drop indexes first
    op.drop_index("ix_job_postings_employer_id", table_name="job_postings")
    op.drop_index("ix_job_postings_status", table_name="job_postings")

    # Drop the table
    op.drop_table("job_postings")

    # ========================================
    # STEP 6: Make employer_id NOT NULL in jobs
    # ========================================

    # Set default employer_id for existing jobs without one
    op.execute("""
        UPDATE jobs 
        SET employer_id = created_by 
        WHERE employer_id IS NULL AND created_by IS NOT NULL
    """)

    # For any remaining NULL employer_id, set to the first employer user
    op.execute("""
        UPDATE jobs 
        SET employer_id = (SELECT id FROM users WHERE role = 'employer' LIMIT 1)
        WHERE employer_id IS NULL
    """)


def downgrade() -> None:
    """
    Reverse the consolidation - recreate job_postings table.
    WARNING: Data migration is not reversible.
    """

    # ========================================
    # STEP 1: Recreate job_postings table
    # ========================================
    op.create_table(
        "job_postings",
        sa.Column(
            "id",
            sa.String(length=36),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("salary_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_currency", sa.String(length=8), nullable=True),
        sa.Column("skills", JSON, nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("employment_type", sa.String(length=50), nullable=True),
        sa.Column("experience_level", sa.String(length=50), nullable=True),
        sa.Column("education", sa.String(length=100), nullable=True),
        sa.Column("benefits", sa.Text(), nullable=True),
        sa.Column("contact_url", sa.String(length=512), nullable=True),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="draft"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_job_postings_status", "job_postings", ["status"])
    op.create_index("ix_job_postings_employer_id", "job_postings", ["employer_id"])

    # ========================================
    # STEP 2: Revert reminder_tasks FK
    # ========================================

    # Drop new FK
    op.drop_constraint("fk_reminder_tasks_job_id", "reminder_tasks", type_="foreignkey")

    # Alter column back to String(36)
    op.alter_column(
        "reminder_tasks",
        "job_id",
        existing_type=sa.Integer(),
        type_=sa.String(36),
        existing_nullable=True,
    )

    # Recreate old FK (note: data will be lost)
    op.create_foreign_key(
        "reminder_tasks_job_id_fkey",
        "reminder_tasks",
        "job_postings",
        ["job_id"],
        ["id"],
    )

    # ========================================
    # STEP 3: Drop added columns from jobs
    # ========================================

    op.drop_constraint("fk_jobs_employer_id", "jobs", type_="foreignkey")
    op.drop_index("ix_jobs_employer_id", table_name="jobs")
    op.drop_column("jobs", "education")
    op.drop_column("jobs", "skills")
    op.drop_column("jobs", "employer_id")

    # ========================================
    # STEP 4: Restore job_code NOT NULL and UNIQUE constraint
    # ========================================

    # First, generate job_code for any rows that don't have one
    op.execute("""
        UPDATE jobs 
        SET job_code = 'JOB-' || LPAD(id::text, 4, '0')
        WHERE job_code IS NULL
    """)

    # Alter job_code back to NOT NULL
    op.alter_column(
        "jobs",
        "job_code",
        existing_type=sa.String(50),
        nullable=False,
    )

    # Recreate UNIQUE constraint
    op.create_unique_constraint("jobs_job_code_key", "jobs", ["job_code"])
