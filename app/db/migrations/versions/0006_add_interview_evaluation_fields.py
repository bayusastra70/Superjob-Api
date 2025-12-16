"""Add AI evaluation fields to interview_sessions

Revision ID: 0006_interview_eval
Revises: 0005_add_activity_types, 0004_add_interview_tables
Create Date: 2025-12-16

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0006_interview_eval"
# Merge both branches: activity types and interview tables
down_revision = ("0005_add_activity_types", "0004_add_interview_tables")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add AI evaluation columns to interview_sessions
    op.add_column(
        "interview_sessions",
        sa.Column("ai_score", sa.Integer(), nullable=True),
    )
    op.add_column(
        "interview_sessions",
        sa.Column("ai_feedback", sa.Text(), nullable=True),
    )
    op.add_column(
        "interview_sessions",
        sa.Column(
            "evaluation_status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
    )
    # Create index on evaluation_status for efficient queries
    op.create_index(
        "ix_interview_sessions_evaluation_status",
        "interview_sessions",
        ["evaluation_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_interview_sessions_evaluation_status", table_name="interview_sessions"
    )
    op.drop_column("interview_sessions", "evaluation_status")
    op.drop_column("interview_sessions", "ai_feedback")
    op.drop_column("interview_sessions", "ai_score")

