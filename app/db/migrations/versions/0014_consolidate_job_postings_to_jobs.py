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
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # Check if job_postings table exists
    tables = inspector.get_table_names()
    job_postings_exists = "job_postings" in tables

    # Check existing columns in jobs table
    existing_columns = [col["name"] for col in inspector.get_columns("jobs")]
    existing_indexes = [idx["name"] for idx in inspector.get_indexes("jobs")]

    # ========================================
    # STEP 1: Add missing columns to jobs table (if not exist)
    # ========================================

    # employer_id - who posted the job
    if "employer_id" not in existing_columns:
        op.add_column(
            "jobs",
            sa.Column("employer_id", sa.Integer(), nullable=True),
        )
        print("✅ Added employer_id column")
    else:
        print("ℹ️ employer_id already exists, skipping...")

    # skills - JSON array of skills
    if "skills" not in existing_columns:
        op.add_column(
            "jobs",
            sa.Column("skills", JSON, nullable=True),
        )
        print("✅ Added skills column")
    else:
        print("ℹ️ skills already exists, skipping...")

    # education - education requirement
    if "education" not in existing_columns:
        op.add_column(
            "jobs",
            sa.Column("education", sa.String(100), nullable=True),
        )
        print("✅ Added education column")
    else:
        print("ℹ️ education already exists, skipping...")

    # Create index for employer_id
    if "ix_jobs_employer_id" not in existing_indexes:
        op.create_index(
            "ix_jobs_employer_id",
            "jobs",
            ["employer_id"],
            unique=False,
        )
        print("✅ Created ix_jobs_employer_id index")
    else:
        print("ℹ️ ix_jobs_employer_id already exists, skipping...")

    # ========================================
    # STEP 1.5: Make job_code nullable (data from job_postings has no job_code)
    # ========================================

    # Check if job_code UNIQUE constraint exists before dropping
    constraints = inspector.get_unique_constraints("jobs")
    constraint_names = [c["name"] for c in constraints]

    if "jobs_job_code_key" in constraint_names:
        op.drop_constraint("jobs_job_code_key", "jobs", type_="unique")
        print("✅ Dropped jobs_job_code_key constraint")
    else:
        print("ℹ️ jobs_job_code_key already dropped, skipping...")

    # Alter job_code to be nullable (safe to run multiple times)
    op.alter_column(
        "jobs",
        "job_code",
        existing_type=sa.String(50),
        nullable=True,
    )

    # ========================================
    # STEP 2: Create FK constraint for employer_id (if not exists)
    # ========================================
    existing_fks = [fk["name"] for fk in inspector.get_foreign_keys("jobs")]

    if "fk_jobs_employer_id" not in existing_fks:
        op.create_foreign_key(
            "fk_jobs_employer_id",
            "jobs",
            "users",
            ["employer_id"],
            ["id"],
        )
        print("✅ Created fk_jobs_employer_id constraint")
    else:
        print("ℹ️ fk_jobs_employer_id already exists, skipping...")

    # ========================================
    # STEP 3: Migrate data from job_postings to jobs WITH MAPPING
    # ========================================

    if job_postings_exists:
        # Check if job_postings has any data
        result = connection.execute(sa.text("SELECT COUNT(*) FROM job_postings"))
        job_postings_count = result.scalar()

        if job_postings_count > 0:
            print(
                f"📦 Migrating {job_postings_count} records from job_postings to jobs..."
            )

            # IMPORTANT: Reset jobs sequence to avoid duplicate key errors
            # when jobs table already has data from seed
            op.execute("""
                SELECT setval(
                    pg_get_serial_sequence('jobs', 'id'),
                    COALESCE((SELECT MAX(id) FROM jobs), 0) + 1,
                    false
                )
            """)
            print("✅ Reset jobs id sequence to avoid duplicates")

            # Create temporary mapping table to preserve UUID -> Integer relationship
            op.execute("""
                CREATE TEMPORARY TABLE IF NOT EXISTS job_id_mapping (
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
            print("✅ Migrated job_postings data to jobs")

            # ========================================
            # STEP 4: Update reminder_tasks foreign key
            # ========================================

            # Check if reminder_tasks has job_id as string type
            reminder_columns = {
                col["name"]: col for col in inspector.get_columns("reminder_tasks")
            }

            if "job_id" in reminder_columns:
                job_id_type = str(reminder_columns["job_id"]["type"])

                if "VARCHAR" in job_id_type or "TEXT" in job_id_type:
                    # Drop old FK constraint from job_postings
                    reminder_fks = [
                        fk["name"]
                        for fk in inspector.get_foreign_keys("reminder_tasks")
                    ]
                    if "reminder_tasks_job_id_fkey" in reminder_fks:
                        op.drop_constraint(
                            "reminder_tasks_job_id_fkey",
                            "reminder_tasks",
                            type_="foreignkey",
                        )

                    # First, add a temporary column to store the new Integer job_id
                    if "job_id_new" not in reminder_columns:
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
                    print("✅ Updated reminder_tasks.job_id to Integer")

            # Create new FK constraint to jobs table (if not exists)
            reminder_fks = [
                fk["name"] for fk in inspector.get_foreign_keys("reminder_tasks")
            ]
            if "fk_reminder_tasks_job_id" not in reminder_fks:
                op.create_foreign_key(
                    "fk_reminder_tasks_job_id",
                    "reminder_tasks",
                    "jobs",
                    ["job_id"],
                    ["id"],
                )
                print("✅ Created fk_reminder_tasks_job_id constraint")

            # Drop the temporary mapping table
            op.execute("DROP TABLE IF EXISTS job_id_mapping")

            # ========================================
            # STEP 5: Drop job_postings table
            # ========================================

            # Drop indexes first (check if they exist)
            jp_indexes = [idx["name"] for idx in inspector.get_indexes("job_postings")]
            if "ix_job_postings_employer_id" in jp_indexes:
                op.drop_index("ix_job_postings_employer_id", table_name="job_postings")
            if "ix_job_postings_status" in jp_indexes:
                op.drop_index("ix_job_postings_status", table_name="job_postings")

            # Drop the table
            op.drop_table("job_postings")
            print("✅ Dropped job_postings table")
        else:
            print("ℹ️ job_postings is empty, dropping table without migration...")
            # Drop indexes first (check if they exist)
            jp_indexes = [idx["name"] for idx in inspector.get_indexes("job_postings")]
            if "ix_job_postings_employer_id" in jp_indexes:
                op.drop_index("ix_job_postings_employer_id", table_name="job_postings")
            if "ix_job_postings_status" in jp_indexes:
                op.drop_index("ix_job_postings_status", table_name="job_postings")
            op.drop_table("job_postings")
            print("✅ Dropped empty job_postings table")
    else:
        print("ℹ️ job_postings table doesn't exist, skipping migration...")

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
