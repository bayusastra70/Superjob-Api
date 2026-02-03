from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0045"
down_revision = "0044"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "candidate_info",
        sa.Column("cv_extracted_profile", postgresql.JSON, nullable=True),
    )
    op.add_column(
        "candidate_info",
        sa.Column("cv_extracted_experience", postgresql.JSON, nullable=True),
    )
    op.add_column(
        "candidate_info",
        sa.Column("cv_extracted_education", postgresql.JSON, nullable=True),
    )
    op.add_column(
        "candidate_info",
        sa.Column("cv_extracted_skills", postgresql.ARRAY(sa.String()), nullable=True),
    )
    op.add_column(
        "candidate_info",
        sa.Column(
            "cv_extracted_languages", postgresql.ARRAY(sa.String()), nullable=True
        ),
    )
    op.add_column(
        "candidate_info",
        sa.Column("cv_extracted_certifications", postgresql.JSON, nullable=True),
    )
    op.add_column(
        "candidate_info",
        sa.Column("cv_extracted_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "candidate_info",
        sa.Column(
            "cv_extraction_status",
            sa.String(20),
            server_default="pending",
            nullable=False,
        ),
    )
    op.add_column(
        "candidate_info", sa.Column("cv_extraction_error", sa.Text, nullable=True)
    )


def downgrade():
    op.drop_column("candidate_info", "cv_extraction_error")
    op.drop_column("candidate_info", "cv_extraction_status")
    op.drop_column("candidate_info", "cv_extracted_at")
    op.drop_column("candidate_info", "cv_extracted_certifications")
    op.drop_column("candidate_info", "cv_extracted_languages")
    op.drop_column("candidate_info", "cv_extracted_skills")
    op.drop_column("candidate_info", "cv_extracted_education")
    op.drop_column("candidate_info", "cv_extracted_experience")
    op.drop_column("candidate_info", "cv_extracted_profile")
