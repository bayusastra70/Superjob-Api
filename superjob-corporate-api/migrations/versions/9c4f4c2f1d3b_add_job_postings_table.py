"""add job postings table"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9c4f4c2f1d3b"
down_revision = "7c9f5b9f4268"
branch_labels = None
depends_on = None


def upgrade() -> None:
    job_status = postgresql.ENUM("draft", "published", "archived", name="job_status")
    job_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "job_postings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=False),
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
                "draft",
                "published",
                "archived",
                name="job_status",
                create_type=False,
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            server_onupdate=sa.text("now()"),
        ),
    )
    op.create_index("ix_job_postings_status", "job_postings", ["status"])
    op.create_index("ix_job_postings_employer_id", "job_postings", ["employer_id"])


def downgrade() -> None:
    op.drop_index("ix_job_postings_employer_id", table_name="job_postings")
    op.drop_index("ix_job_postings_status", table_name="job_postings")
    op.drop_table("job_postings")
    op.execute("DROP TYPE IF EXISTS job_status")
