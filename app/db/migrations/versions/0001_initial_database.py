"""Initial database migration

Revision ID: 0001_initial_database
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = "0001_initial_database"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========== AKTIFKAN EXTENSION UUID ==========
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ========== CREATE ENUM TYPES (SAFE VERSION) ==========
    op.execute("""
    DO $$ 
    BEGIN 
        CREATE TYPE reminder_task_status AS ENUM ('pending', 'done', 'ignored');
    EXCEPTION 
        WHEN duplicate_object THEN 
            NULL;
    END $$;
    """)

    op.execute("""
    DO $$ 
    BEGIN 
        CREATE TYPE reminder_task_type AS ENUM ('message', 'candidate', 'job_update', 'interview', 'other');
    EXCEPTION 
        WHEN duplicate_object THEN 
            NULL;
    END $$;
    """)

    op.execute("""
    DO $$ 
    BEGIN 
        CREATE TYPE activity_type AS ENUM (
            'new_applicant', 
            'status_update', 
            'new_message', 
            'job_performance_alert', 
            'system_event'
        );
    EXCEPTION 
        WHEN duplicate_object THEN 
            NULL;
    END $$;
    """)

    op.execute("""
    DO $$ 
    BEGIN 
        CREATE TYPE job_status AS ENUM ('draft', 'published', 'archived');
    EXCEPTION 
        WHEN duplicate_object THEN 
            NULL;
    END $$;
    """)

    op.execute("""
    DO $$ 
    BEGIN 
        CREATE TYPE user_role AS ENUM ('admin', 'employer', 'candidate');
    EXCEPTION 
        WHEN duplicate_object THEN 
            NULL;
    END $$;
    """)

    # ========== CREATE USERS TABLE ==========
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM(
                "admin", "employer", "candidate", name="user_role", create_type=False
            ),
            nullable=False,
            server_default="candidate",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default="false"),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("idx_users_email", "users", ["email"], unique=True)
    op.create_index("idx_users_username", "users", ["username"], unique=True)

    # ========== CREATE COMPANIES TABLE (FIXED UUID) ==========
    op.create_table(
        "companies",
        sa.Column(
            "id",
            sa.String(length=36),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),  # ← PAKAI uuid_generate_v4()
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("industry", sa.String(length=100), nullable=False),
        sa.Column("website", sa.String(length=255), nullable=False),
        sa.Column("location", sa.Text(), nullable=False),
        sa.Column("logo_url", sa.String(length=255), nullable=False),
        sa.Column("founded_year", sa.Integer(), nullable=True),
        sa.Column("employee_size", sa.String(length=255), nullable=True),
        sa.Column("linkedin_url", sa.String(length=255), nullable=False),
        sa.Column("twitter_url", sa.String(length=255), nullable=False),
        sa.Column("instagram_url", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_companies_id"), "companies", ["id"], unique=False)
    op.create_index(op.f("ix_companies_name"), "companies", ["name"], unique=True)

    # ========== CREATE COMPANY_REVIEWS TABLE (FIXED UUID) ==========
    op.create_table(
        "company_reviews",
        sa.Column(
            "id",
            sa.String(length=36),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),  # ← PAKAI uuid_generate_v4()
        sa.Column("company_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("pros", sa.Text(), nullable=False),
        sa.Column("cons", sa.Text(), nullable=False),
        sa.Column("position", sa.String(length=255), nullable=False),
        sa.Column("employment_status", sa.String(length=255), nullable=False),
        sa.Column("employment_duration", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_company_reviews_company_id"),
        "company_reviews",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_company_reviews_created_at"),
        "company_reviews",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_company_reviews_id"), "company_reviews", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_company_reviews_rating"), "company_reviews", ["rating"], unique=False
    )

    # ========== CREATE JOBS TABLE ==========
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("location", sa.String(length=100), nullable=True),
        sa.Column("employment_type", sa.String(length=50), nullable=True),
        sa.Column("experience_level", sa.String(length=50), nullable=True),
        sa.Column("education_requirement", sa.String(length=100), nullable=True),
        sa.Column("salary_range", sa.String(length=100), nullable=True),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="open"
        ),
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
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_code"),
    )
    op.create_index("idx_jobs_status", "jobs", ["status"], unique=False)
    op.create_index("idx_jobs_department", "jobs", ["department"], unique=False)

    # ========== CREATE JOB_POSTINGS TABLE (FIXED UUID & ENUM) ==========
    op.create_table(
        "job_postings",
        sa.Column(
            "id",
            sa.String(length=36),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),  # ← PAKAI uuid_generate_v4()
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("salary_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_currency", sa.String(length=8), nullable=True),
        sa.Column("skills", sa.JSON(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("employment_type", sa.String(length=50), nullable=True),
        sa.Column("experience_level", sa.String(length=50), nullable=True),
        sa.Column("education", sa.String(length=100), nullable=True),
        sa.Column("benefits", sa.Text(), nullable=True),
        sa.Column("contact_url", sa.String(length=512), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["employer_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_postings_status", "job_postings", ["status"])
    op.create_index("ix_job_postings_employer_id", "job_postings", ["employer_id"])

    # ========== CREATE APPLICATIONS TABLE ==========
    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("candidate_name", sa.String(length=255), nullable=False),
        sa.Column("candidate_email", sa.String(length=255), nullable=False),
        sa.Column("candidate_phone", sa.String(length=50), nullable=True),
        sa.Column("candidate_linkedin", sa.String(length=255), nullable=True),
        sa.Column("candidate_cv_url", sa.Text(), nullable=True),
        sa.Column("candidate_education", sa.String(length=100), nullable=True),
        sa.Column("candidate_experience_years", sa.Integer(), nullable=True),
        sa.Column("current_company", sa.String(length=255), nullable=True),
        sa.Column("current_position", sa.String(length=255), nullable=True),
        sa.Column("expected_salary", sa.String(length=100), nullable=True),
        sa.Column("notice_period", sa.String(length=50), nullable=True),
        sa.Column(
            "application_status",
            sa.String(length=50),
            nullable=False,
            server_default="applied",
        ),
        sa.Column("interview_stage", sa.String(length=50), nullable=True),
        sa.Column("interview_scheduled_by", sa.String(length=100), nullable=True),
        sa.Column("interview_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fit_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("skill_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("experience_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("overall_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.Column(
            "applied_date",
            sa.Date(),
            server_default=sa.text("CURRENT_DATE"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_applications_job_id", "applications", ["job_id"])
    op.create_index("idx_applications_status", "applications", ["application_status"])
    op.create_index("idx_applications_stage", "applications", ["interview_stage"])
    op.create_index("idx_applications_score", "applications", ["overall_score"])

    # ========== CREATE CANDIDATE_APPLICATION TABLE ==========
    op.create_table(
        "candidate_application",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("applied_position", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column(
            "applied_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_candidate_application_id", "candidate_application", ["id"])
    op.create_index(
        "ix_candidate_application_email",
        "candidate_application",
        ["email"],
        unique=True,
    )

    # ========== CREATE REJECTION_REASONS TABLE ==========
    op.create_table(
        "rejection_reasons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reason_code", sa.String(length=50), nullable=False),
        sa.Column("reason_text", sa.Text(), nullable=False),
        sa.Column("is_custom", sa.Boolean(), nullable=True, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=True, server_default="true"),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("reason_code"),
    )
    op.create_index("ix_rejection_reasons_id", "rejection_reasons", ["id"])
    op.create_index(
        "ix_rejection_reasons_reason_code",
        "rejection_reasons",
        ["reason_code"],
        unique=True,
    )

    # ========== ADD FOREIGN KEY TO CANDIDATE_APPLICATION ==========
    with op.batch_alter_table("candidate_application", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("rejection_reason_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_candidate_application_rejection_reason",
            "rejection_reasons",
            ["rejection_reason_id"],
            ["id"],
        )

    # ========== CREATE CANDIDATE_SCORE TABLE ==========
    op.create_table(
        "candidate_score",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("candidate_name", sa.String(length=255), nullable=True),
        sa.Column("fit_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("skill_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("experience_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("education_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("reasons", sa.JSON(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("application_id"),
    )
    op.create_index(
        "idx_candidate_score_application", "candidate_score", ["application_id"]
    )
    op.create_index("idx_candidate_score_job", "candidate_score", ["job_id"])
    op.create_index("idx_candidate_score_fit", "candidate_score", ["fit_score"])

    # ========== CREATE APPLICATION_HISTORY TABLE ==========
    op.create_table(
        "application_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("changed_by", sa.Integer(), nullable=True),
        sa.Column("previous_status", sa.String(length=50), nullable=True),
        sa.Column("new_status", sa.String(length=50), nullable=True),
        sa.Column("previous_stage", sa.String(length=50), nullable=True),
        sa.Column("new_stage", sa.String(length=50), nullable=True),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column(
            "change_date",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
        ),
        sa.ForeignKeyConstraint(
            ["changed_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_app_history_application", "application_history", ["application_id"]
    )

    # ========== CREATE CHAT_THREADS TABLE (FIXED UUID) ==========
    op.create_table(
        "chat_threads",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("candidate_id", sa.Integer(), nullable=False),
        sa.Column("candidate_name", sa.String(length=255), nullable=True),
        sa.Column("job_title", sa.String(length=255), nullable=True),
        sa.Column("last_message", sa.Text(), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "unread_count_employer", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "unread_count_candidate", sa.Integer(), nullable=False, server_default="0"
        ),
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
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["employer_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_chat_threads_application", "chat_threads", ["application_id"])
    op.create_index(
        "idx_chat_threads_users", "chat_threads", ["employer_id", "candidate_id"]
    )
    op.create_index("idx_chat_threads_job", "chat_threads", ["job_id"])
    op.create_index("idx_chat_threads_updated", "chat_threads", ["updated_at"])

    # ========== CREATE MESSAGES TABLE (FIXED UUID) ==========
    op.create_table(
        "messages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("thread_id", sa.String(length=36), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("receiver_id", sa.Integer(), nullable=False),
        sa.Column("sender_name", sa.String(length=255), nullable=True),
        sa.Column("receiver_name", sa.String(length=255), nullable=True),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="sent"
        ),
        sa.Column("is_ai_suggestion", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ai_suggestions", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('sent', 'delivered', 'seen', 'failed')",
            name="check_message_status",
        ),
        sa.ForeignKeyConstraint(
            ["receiver_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["sender_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["thread_id"],
            ["chat_threads.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_messages_thread", "messages", ["thread_id", "created_at"])
    op.create_index("idx_messages_sender", "messages", ["sender_id", "created_at"])
    op.create_index(
        "idx_messages_status", "messages", ["thread_id", "receiver_id", "status"]
    )
    op.create_index(
        "idx_messages_receiver", "messages", ["receiver_id", "status", "created_at"]
    )

    # ========== CREATE DASHBOARD_SEEN TABLE ==========
    op.create_table(
        "dashboard_seen",
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("item_key", sa.String(length=50), nullable=False),
        sa.Column(
            "seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["employer_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("employer_id", "item_key"),
    )

    # ========== CREATE JOB_PERFORMANCE_DAILY TABLE ==========
    op.create_table(
        "job_performance_daily",
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("job_title", sa.String(length=255), nullable=True),
        sa.Column("views_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("applicants_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("apply_rate", sa.Numeric(6, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(
            ["employer_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
        ),
        sa.PrimaryKeyConstraint("job_id", "as_of_date"),
    )
    op.create_index(
        "ix_job_performance_daily_employer_date",
        "job_performance_daily",
        ["employer_id", "as_of_date"],
    )

    # ========== CREATE ACTIVITY_LOGS TABLE (FIXED ENUM) ==========
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM(
                "new_applicant",
                "status_update",
                "new_message",
                "job_performance_alert",
                "system_event",
                name="activity_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("subtitle", sa.Text(), nullable=True),
        sa.Column("meta_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("applicant_id", sa.Integer(), nullable=True),
        sa.Column("message_id", sa.String(length=64), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(
            ["applicant_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["employer_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activity_logs_applicant_id", "activity_logs", ["applicant_id"])
    op.create_index("ix_activity_logs_employer", "activity_logs", ["employer_id"])
    op.create_index("ix_activity_logs_is_read", "activity_logs", ["is_read"])
    op.create_index("ix_activity_logs_job_id", "activity_logs", ["job_id"])
    op.create_index("ix_activity_logs_message_id", "activity_logs", ["message_id"])
    op.create_index("ix_activity_logs_timestamp_desc", "activity_logs", ["timestamp"])
    op.create_index("ix_activity_logs_type", "activity_logs", ["type"])

    # ========== CREATE REMINDER_TASKS TABLE (FIXED UUID & ENUMS) ==========
    op.create_table(
        "reminder_tasks",
        sa.Column(
            "id",
            sa.String(length=36),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),  # ← PAKAI uuid_generate_v4()
        sa.Column("employer_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=True),
        sa.Column("candidate_id", sa.Integer(), nullable=True),
        sa.Column("task_title", sa.String(length=255), nullable=False),
        sa.Column(
            "task_type",
            postgresql.ENUM(
                "message",
                "candidate",
                "job_update",
                "interview",
                "other",
                name="reminder_task_type",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("redirect_url", sa.String(length=1024), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM(
                "pending",
                "done",
                "ignored",
                name="reminder_task_status",
                create_type=False,
            ),
            nullable=False,
            server_default="pending",
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
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["employer_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["job_postings.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reminder_tasks_due_at", "reminder_tasks", ["due_at"])
    op.create_index("ix_reminder_tasks_employer_id", "reminder_tasks", ["employer_id"])
    op.create_index(
        "ix_reminder_tasks_employer_status", "reminder_tasks", ["employer_id", "status"]
    )

    # ========== CREATE JOB_VIEWS TABLE ==========
    op.create_table(
        "job_views",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column(
            "viewed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            ["jobs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_views_job_id", "job_views", ["job_id"])
    op.create_index("ix_job_views_viewed_at", "job_views", ["viewed_at"])

    # ========== CREATE AUDIT_LOG TABLE ==========
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("entity", sa.String(), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("details", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_log_id", "audit_log", ["id"])

    # ========== CREATE NOTIFICATIONS TABLE (FIXED UUID) ==========
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "notification_type",
            sa.String(length=50),
            nullable=False,
            server_default="message",
        ),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("thread_id", sa.String(length=255), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["thread_id"],
            ["chat_threads.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ========== CREATE USER_DEVICES TABLE (FIXED UUID) ==========
    op.create_table(
        "user_devices",
        sa.Column("id", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("device_token", sa.Text(), nullable=False),
        sa.Column("device_type", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # =========== CREATE iNTERVIEW RATING & FEEDBACK TABLE ==============
    op.create_table(
        "interview_feedbacks",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "application_id",
            sa.Integer(),
            sa.ForeignKey("applications.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("feedback", sa.String(500), nullable=True),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=False,
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
        # Check constraint for rating 1-5
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
        # Check constraint for feedback min 10 chars (if not null)
        sa.CheckConstraint(
            "feedback IS NULL OR length(feedback) >= 10",
            name="check_feedback_min_length",
        ),
    )

    # Create index for faster lookups
    op.create_index(
        "ix_interview_feedbacks_application_id",
        "interview_feedbacks",
        ["application_id"],
    )
    op.create_index(
        "ix_interview_feedbacks_created_by", "interview_feedbacks", ["created_by"]
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("user_devices")
    op.drop_table("notifications")
    op.drop_index("ix_audit_log_id", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_index("ix_job_views_viewed_at", table_name="job_views")
    op.drop_index("ix_job_views_job_id", table_name="job_views")
    op.drop_table("job_views")
    op.drop_index("ix_reminder_tasks_employer_status", table_name="reminder_tasks")
    op.drop_index("ix_reminder_tasks_employer_id", table_name="reminder_tasks")
    op.drop_index("ix_reminder_tasks_due_at", table_name="reminder_tasks")
    op.drop_table("reminder_tasks")
    op.drop_index("ix_activity_logs_type", table_name="activity_logs")
    op.drop_index("ix_activity_logs_timestamp_desc", table_name="activity_logs")
    op.drop_index("ix_activity_logs_message_id", table_name="activity_logs")
    op.drop_index("ix_activity_logs_job_id", table_name="activity_logs")
    op.drop_index("ix_activity_logs_is_read", table_name="activity_logs")
    op.drop_index("ix_activity_logs_employer", table_name="activity_logs")
    op.drop_index("ix_activity_logs_applicant_id", table_name="activity_logs")
    op.drop_table("activity_logs")
    op.drop_index(
        "ix_job_performance_daily_employer_date", table_name="job_performance_daily"
    )
    op.drop_table("job_performance_daily")
    op.drop_table("dashboard_seen")
    op.drop_index("idx_messages_receiver", table_name="messages")
    op.drop_index("idx_messages_status", table_name="messages")
    op.drop_index("idx_messages_sender", table_name="messages")
    op.drop_index("idx_messages_thread", table_name="messages")
    op.drop_table("messages")
    op.drop_index("idx_chat_threads_updated", table_name="chat_threads")
    op.drop_index("idx_chat_threads_job", table_name="chat_threads")
    op.drop_index("idx_chat_threads_users", table_name="chat_threads")
    op.drop_index("idx_chat_threads_application", table_name="chat_threads")
    op.drop_table("chat_threads")
    op.drop_index("idx_app_history_application", table_name="application_history")
    op.drop_table("application_history")
    op.drop_index("idx_candidate_score_fit", table_name="candidate_score")
    op.drop_index("idx_candidate_score_job", table_name="candidate_score")
    op.drop_index("idx_candidate_score_application", table_name="candidate_score")
    op.drop_table("candidate_score")
    op.drop_index("ix_interview_feedbacks_created_by")
    op.drop_index("ix_interview_feedbacks_application_id")
    op.drop_table("interview_feedbacks")

    # ========== HAPUS FOREIGN KEY TERLEBIH DAHULU ==========
    with op.batch_alter_table("candidate_application", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_candidate_application_rejection_reason", type_="foreignkey"
        )
        batch_op.drop_column("rejection_reason_id")

    op.drop_index("ix_rejection_reasons_reason_code", table_name="rejection_reasons")
    op.drop_index("ix_rejection_reasons_id", table_name="rejection_reasons")
    op.drop_table("rejection_reasons")

    # ========== LANJUTKAN YANG LAIN ==========
    op.drop_index("ix_candidate_application_email", table_name="candidate_application")
    op.drop_index("ix_candidate_application_id", table_name="candidate_application")
    op.drop_table("candidate_application")
    op.drop_index("idx_applications_score", table_name="applications")
    op.drop_index("idx_applications_stage", table_name="applications")
    op.drop_index("idx_applications_status", table_name="applications")
    op.drop_index("idx_applications_job_id", table_name="applications")
    op.drop_table("applications")
    op.drop_index("ix_job_postings_employer_id", table_name="job_postings")
    op.drop_index("ix_job_postings_status", table_name="job_postings")
    op.drop_table("job_postings")
    op.drop_index("idx_jobs_department", table_name="jobs")
    op.drop_index("idx_jobs_status", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index(op.f("ix_company_reviews_rating"), table_name="company_reviews")
    op.drop_index(op.f("ix_company_reviews_id"), table_name="company_reviews")
    op.drop_index(op.f("ix_company_reviews_created_at"), table_name="company_reviews")
    op.drop_index(op.f("ix_company_reviews_company_id"), table_name="company_reviews")
    op.drop_table("company_reviews")
    op.drop_index(op.f("ix_companies_name"), table_name="companies")
    op.drop_index(op.f("ix_companies_id"), table_name="companies")
    op.drop_table("companies")
    op.drop_index("idx_users_username", table_name="users")
    op.drop_index("idx_users_email", table_name="users")
    op.drop_table("users")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS reminder_task_status")
    op.execute("DROP TYPE IF EXISTS reminder_task_type")
    op.execute("DROP TYPE IF EXISTS activity_type")
    op.execute("DROP TYPE IF EXISTS job_status")
    op.execute("DROP TYPE IF EXISTS user_role")

    # Drop extension
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
