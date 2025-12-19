"""Consolidate jobs and job_postings tables into unified jobs table

This migration:
1. Creates new unified jobs table with structure from job_postings but Integer ID
2. Migrates data from both jobs and job_postings tables
3. Updates all foreign key references
4. Drops old tables

Revision ID: 0012_consolidate_jobs_tables
Revises: 0011_add_job_posting_new_fields
Create Date: 2025-12-19
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0012_consolidate_jobs_tables"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========== STEP 1: Create new unified jobs table ==========
    # First drop indexes from old jobs table to avoid naming conflicts
    op.execute("DROP INDEX IF EXISTS ix_jobs_employer_id")
    op.execute("DROP INDEX IF EXISTS ix_jobs_status")
    op.execute("DROP INDEX IF EXISTS ix_jobs_company_id")
    op.execute("DROP INDEX IF EXISTS ix_jobs_created_at")
    op.execute("DROP INDEX IF EXISTS idx_jobs_status")
    op.execute("DROP INDEX IF EXISTS idx_jobs_department")

    # Rename old jobs table
    op.rename_table("jobs", "jobs_old")

    # Create new jobs table with job_postings structure + Integer ID
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        # Step 1: Informasi Dasar Pekerjaan (from job_postings)
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("major", sa.String(100), nullable=True),
        sa.Column(
            "working_type",
            postgresql.ENUM(
                "onsite", "remote", "hybrid", name="working_type", create_type=False
            ),
            nullable=True,
            server_default="onsite",
        ),
        sa.Column(
            "gender_requirement",
            postgresql.ENUM(
                "any", "male", "female", name="gender_requirement", create_type=False
            ),
            nullable=True,
            server_default="any",
        ),
        sa.Column("min_age", sa.Integer(), nullable=True),
        sa.Column("max_age", sa.Integer(), nullable=True),
        # Salary fields (Numeric - more precise)
        sa.Column("salary_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_currency", sa.String(8), nullable=True, server_default="IDR"),
        sa.Column(
            "salary_interval",
            postgresql.ENUM(
                "hourly",
                "daily",
                "weekly",
                "monthly",
                "yearly",
                name="salary_interval",
                create_type=False,
            ),
            nullable=True,
            server_default="monthly",
        ),
        # Other fields
        sa.Column("skills", sa.JSON(), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("employment_type", sa.String(50), nullable=True),
        sa.Column("experience_level", sa.String(50), nullable=True),
        sa.Column("education", sa.String(100), nullable=True),
        # Step 2: Persyaratan (from job_postings)
        sa.Column("responsibilities", sa.Text(), nullable=True),
        sa.Column("qualifications", sa.Text(), nullable=True),
        sa.Column("benefits", sa.Text(), nullable=True),
        # Step 3: AI Interview Settings (from job_postings)
        sa.Column(
            "ai_interview_enabled", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("ai_interview_questions_count", sa.Integer(), nullable=True),
        sa.Column("ai_interview_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("ai_interview_deadline_days", sa.Integer(), nullable=True),
        sa.Column("ai_interview_questions", sa.Text(), nullable=True),
        # Other fields
        sa.Column("contact_url", sa.String(512), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "draft", "published", "archived", name="job_status", create_type=False
            ),
            nullable=False,
            server_default="draft",
        ),
        # Legacy fields from old jobs table (untuk kompatibilitas)
        sa.Column("job_code", sa.String(50), nullable=True),  # Optional now
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("requirements", sa.Text(), nullable=True),  # Alias to qualifications
        sa.Column("created_by", sa.Integer(), nullable=True),
        # Company relation (from migration 0010) - BigInteger after 0009 migration
        sa.Column("company_id", sa.BigInteger(), nullable=True),
        # Timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        # Constraints
        sa.ForeignKeyConstraint(["employer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        # Note: company_id FK constraint handled separately due to migration order issues
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("ix_jobs_employer_id", "jobs", ["employer_id"])
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_index("ix_jobs_company_id", "jobs", ["company_id"])
    op.create_index("ix_jobs_created_at", "jobs", ["created_at"])

    # ========== STEP 2: Migrate data from jobs_old ==========
    # The old jobs table has Integer IDs 1-8
    op.execute("""
    INSERT INTO jobs (
        id, employer_id, title, description, 
        location, employment_type, experience_level, education,
        status, job_code, department, requirements, responsibilities,
        created_by, created_at, updated_at
    )
    SELECT 
        id, 
        COALESCE(created_by, 1) as employer_id,  -- Use creator as employer, default to admin
        title, 
        description,
        location, 
        employment_type, 
        experience_level, 
        education_requirement as education,
        CASE 
            WHEN status = 'open' THEN 'published'::job_status
            WHEN status = 'closed' THEN 'archived'::job_status
            ELSE 'draft'::job_status
        END as status,
        job_code,
        department,
        requirements,
        responsibilities,
        created_by,
        created_at,
        updated_at
    FROM jobs_old;
    """)

    # ========== STEP 3: Migrate data from job_postings ==========
    # job_postings has UUID IDs, we need to convert them to Integer IDs
    # We'll use a sequence starting from 100 to avoid conflict with existing jobs
    op.execute("""
    INSERT INTO jobs (
        id, employer_id, title, description,
        industry, major, working_type, gender_requirement, min_age, max_age,
        salary_min, salary_max, salary_currency, salary_interval,
        skills, location, employment_type, experience_level, education,
        responsibilities, qualifications, benefits,
        ai_interview_enabled, ai_interview_questions_count, 
        ai_interview_duration_seconds, ai_interview_deadline_days, ai_interview_questions,
        contact_url, status, created_at, updated_at
    )
    SELECT 
        100 + ROW_NUMBER() OVER (ORDER BY created_at) as id,
        employer_id,
        title,
        description,
        industry,
        major,
        working_type,
        gender_requirement,
        min_age,
        max_age,
        salary_min,
        salary_max,
        salary_currency,
        salary_interval,
        skills,
        location,
        employment_type,
        experience_level,
        education,
        responsibilities,
        qualifications,
        benefits,
        ai_interview_enabled,
        ai_interview_questions_count,
        ai_interview_duration_seconds,
        ai_interview_deadline_days,
        ai_interview_questions,
        contact_url,
        status,
        created_at,
        updated_at
    FROM job_postings;
    """)

    # Update sequence to avoid ID conflicts
    op.execute("""
    SELECT setval(pg_get_serial_sequence('jobs', 'id'), 
           (SELECT COALESCE(MAX(id), 1) FROM jobs));
    """)

    # ========== STEP 4: Create mapping table for job_postings UUID -> Integer ==========
    # This is needed to update foreign keys in reminder_tasks
    op.execute("""
    CREATE TEMP TABLE job_id_mapping AS
    SELECT 
        jp.id as old_uuid_id,
        100 + ROW_NUMBER() OVER (ORDER BY jp.created_at) as new_int_id
    FROM job_postings jp;
    """)

    # ========== STEP 5: Update reminder_tasks to use Integer job_id ==========
    # First, alter the column type
    op.execute("""
    ALTER TABLE reminder_tasks 
    DROP CONSTRAINT IF EXISTS reminder_tasks_job_id_fkey;
    """)

    # Update the values using mapping
    op.execute("""
    UPDATE reminder_tasks rt
    SET job_id = m.new_int_id::text
    FROM job_id_mapping m
    WHERE rt.job_id = m.old_uuid_id;
    """)

    # Change column type from String(36) to Integer
    op.execute("""
    ALTER TABLE reminder_tasks 
    ALTER COLUMN job_id TYPE INTEGER USING job_id::integer;
    """)

    # Re-add foreign key constraint for reminder_tasks
    op.execute("""
    ALTER TABLE reminder_tasks
    ADD CONSTRAINT reminder_tasks_job_id_fkey 
    FOREIGN KEY (job_id) REFERENCES jobs(id);
    """)

    # ========== STEP 6: Handle all other dependent tables ==========
    # These tables have FK to old jobs table with INTEGER job_id
    dependent_tables = [
        ("applications", "applications_job_id_fkey"),
        ("candidate_score", "candidate_score_job_id_fkey"),
        ("chat_threads", "chat_threads_job_id_fkey"),
        ("job_performance_daily", "job_performance_daily_job_id_fkey"),
        ("activity_logs", "activity_logs_job_id_fkey"),
        ("job_views", "job_views_job_id_fkey"),
    ]

    # Drop all foreign key constraints
    for table_name, constraint_name in dependent_tables:
        op.execute(f"""
        ALTER TABLE {table_name} 
        DROP CONSTRAINT IF EXISTS {constraint_name};
        """)

    # Re-add foreign key constraints to new jobs table
    for table_name, constraint_name in dependent_tables:
        op.execute(f"""
        ALTER TABLE {table_name}
        ADD CONSTRAINT {constraint_name}
        FOREIGN KEY (job_id) REFERENCES jobs(id);
        """)

    # ========== STEP 7: Clean up temp table ==========
    op.execute("DROP TABLE IF EXISTS job_id_mapping;")

    # ========== STEP 8: Drop old tables ==========
    op.execute("DROP INDEX IF EXISTS ix_job_postings_status")
    op.execute("DROP INDEX IF EXISTS ix_job_postings_employer_id")
    op.drop_table("job_postings")
    op.drop_table("jobs_old")


def downgrade() -> None:
    # WARNING: Downgrade will lose data structure improvements
    # This is a complex migration, downgrade should be done carefully

    # Recreate job_postings table
    op.create_table(
        "job_postings",
        sa.Column(
            "id",
            sa.String(36),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("major", sa.String(100), nullable=True),
        sa.Column(
            "working_type",
            postgresql.ENUM(
                "onsite", "remote", "hybrid", name="working_type", create_type=False
            ),
            nullable=True,
        ),
        sa.Column(
            "gender_requirement",
            postgresql.ENUM(
                "any", "male", "female", name="gender_requirement", create_type=False
            ),
            nullable=True,
        ),
        sa.Column("min_age", sa.Integer(), nullable=True),
        sa.Column("max_age", sa.Integer(), nullable=True),
        sa.Column("salary_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_currency", sa.String(8), nullable=True),
        sa.Column(
            "salary_interval",
            postgresql.ENUM(
                "hourly",
                "daily",
                "weekly",
                "monthly",
                "yearly",
                name="salary_interval",
                create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("skills", sa.JSON(), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("employment_type", sa.String(50), nullable=True),
        sa.Column("experience_level", sa.String(50), nullable=True),
        sa.Column("education", sa.String(100), nullable=True),
        sa.Column("responsibilities", sa.Text(), nullable=True),
        sa.Column("qualifications", sa.Text(), nullable=True),
        sa.Column("benefits", sa.Text(), nullable=True),
        sa.Column(
            "ai_interview_enabled", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("ai_interview_questions_count", sa.Integer(), nullable=True),
        sa.Column("ai_interview_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("ai_interview_deadline_days", sa.Integer(), nullable=True),
        sa.Column("ai_interview_questions", sa.Text(), nullable=True),
        sa.Column("contact_url", sa.String(512), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "draft", "published", "archived", name="job_status", create_type=False
            ),
            nullable=False,
            server_default="draft",
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

    # Recreate old jobs table structure
    op.rename_table("jobs", "jobs_new")

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_code", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column("location", sa.String(100), nullable=True),
        sa.Column("employment_type", sa.String(50), nullable=True),
        sa.Column("experience_level", sa.String(50), nullable=True),
        sa.Column("education_requirement", sa.String(100), nullable=True),
        sa.Column("salary_range", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("requirements", sa.Text(), nullable=True),
        sa.Column("responsibilities", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_code"),
    )

    # Migrate back (simplified - may lose some data)
    op.execute("""
    INSERT INTO jobs (id, job_code, title, department, location, employment_type, 
                      experience_level, education_requirement, status, description, 
                      requirements, responsibilities, created_by, created_at, updated_at)
    SELECT 
        id,
        COALESCE(job_code, 'JOB_' || id),
        title,
        department,
        location,
        employment_type,
        experience_level,
        education,
        CASE 
            WHEN status::text = 'published' THEN 'open'
            WHEN status::text = 'archived' THEN 'closed'
            ELSE 'draft'
        END,
        description,
        COALESCE(requirements, qualifications),
        responsibilities,
        created_by,
        created_at,
        updated_at
    FROM jobs_new
    WHERE id < 100;  -- Original jobs data
    """)

    # Update reminder_tasks back to String
    op.execute("""
    ALTER TABLE reminder_tasks 
    DROP CONSTRAINT IF EXISTS reminder_tasks_job_id_fkey;
    """)
    op.execute("""
    ALTER TABLE reminder_tasks 
    ALTER COLUMN job_id TYPE VARCHAR(36) USING job_id::text;
    """)

    op.drop_table("jobs_new")

    # Recreate indexes
    op.create_index("idx_jobs_status", "jobs", ["status"])
    op.create_index("idx_jobs_department", "jobs", ["department"])
    op.create_index("ix_job_postings_status", "job_postings", ["status"])
    op.create_index("ix_job_postings_employer_id", "job_postings", ["employer_id"])
