"""Add new fields to job_postings table for complete UI flow support

Revision ID: 0011
Revises: 0010
Create Date: 2024-12-19

Fields added:
- Step 1: industry, major, working_type, gender_requirement, min_age, max_age, salary_interval
- Step 2: qualifications (responsibilities and benefits already exist)
- Step 3: ai_interview_enabled, ai_interview_questions_count, ai_interview_duration_seconds,
         ai_interview_deadline_days, ai_interview_questions
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types first
    working_type_enum = sa.Enum("onsite", "remote", "hybrid", name="working_type")
    gender_requirement_enum = sa.Enum(
        "any", "male", "female", name="gender_requirement"
    )
    salary_interval_enum = sa.Enum(
        "hourly", "daily", "weekly", "monthly", "yearly", name="salary_interval"
    )

    # Create enums in database
    working_type_enum.create(op.get_bind(), checkfirst=True)
    gender_requirement_enum.create(op.get_bind(), checkfirst=True)
    salary_interval_enum.create(op.get_bind(), checkfirst=True)

    # === Step 1: Informasi Dasar Pekerjaan ===
    op.add_column("job_postings", sa.Column("industry", sa.String(100), nullable=True))
    op.add_column("job_postings", sa.Column("major", sa.String(100), nullable=True))
    op.add_column(
        "job_postings",
        sa.Column(
            "working_type", working_type_enum, nullable=True, server_default="onsite"
        ),
    )
    op.add_column(
        "job_postings",
        sa.Column(
            "gender_requirement",
            gender_requirement_enum,
            nullable=True,
            server_default="any",
        ),
    )
    op.add_column("job_postings", sa.Column("min_age", sa.Integer(), nullable=True))
    op.add_column("job_postings", sa.Column("max_age", sa.Integer(), nullable=True))
    op.add_column(
        "job_postings",
        sa.Column(
            "salary_interval",
            salary_interval_enum,
            nullable=True,
            server_default="monthly",
        ),
    )

    # Update salary_currency default if not set
    op.alter_column(
        "job_postings",
        "salary_currency",
        existing_type=sa.String(8),
        server_default="IDR",
    )

    # === Step 2: Persyaratan ===
    op.add_column(
        "job_postings", sa.Column("responsibilities", sa.Text(), nullable=True)
    )
    op.add_column("job_postings", sa.Column("qualifications", sa.Text(), nullable=True))

    # === Step 3: AI Interview Settings ===
    op.add_column(
        "job_postings",
        sa.Column(
            "ai_interview_enabled", sa.Boolean(), nullable=False, server_default="false"
        ),
    )
    op.add_column(
        "job_postings",
        sa.Column("ai_interview_questions_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "job_postings",
        sa.Column("ai_interview_duration_seconds", sa.Integer(), nullable=True),
    )
    op.add_column(
        "job_postings",
        sa.Column("ai_interview_deadline_days", sa.Integer(), nullable=True),
    )
    op.add_column(
        "job_postings", sa.Column("ai_interview_questions", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    # === Step 3: AI Interview Settings ===
    op.drop_column("job_postings", "ai_interview_questions")
    op.drop_column("job_postings", "ai_interview_deadline_days")
    op.drop_column("job_postings", "ai_interview_duration_seconds")
    op.drop_column("job_postings", "ai_interview_questions_count")
    op.drop_column("job_postings", "ai_interview_enabled")

    # === Step 2: Persyaratan ===
    op.drop_column("job_postings", "qualifications")
    op.drop_column("job_postings", "responsibilities")

    # === Step 1: Informasi Dasar Pekerjaan ===
    op.drop_column("job_postings", "salary_interval")
    op.drop_column("job_postings", "max_age")
    op.drop_column("job_postings", "min_age")
    op.drop_column("job_postings", "gender_requirement")
    op.drop_column("job_postings", "working_type")
    op.drop_column("job_postings", "major")
    op.drop_column("job_postings", "industry")

    # Drop enum types
    sa.Enum(name="salary_interval").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="gender_requirement").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="working_type").drop(op.get_bind(), checkfirst=True)
