"""Add current_question_id to interview_sessions for explicit question tracking

Revision ID: 0007_current_question_id
Revises: 0006_interview_eval
Create Date: 2025-12-19

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0007_current_question_id"
down_revision = "0006_interview_eval"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add current_question_id column to track the active question explicitly
    op.add_column(
        "interview_sessions",
        sa.Column("current_question_id", sa.Integer(), nullable=True),
    )
    # Add foreign key constraint with use_alter to handle circular dependency
    op.create_foreign_key(
        "fk_interview_sessions_current_question_id",
        "interview_sessions",
        "interview_messages",
        ["current_question_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_interview_sessions_current_question_id",
        "interview_sessions",
        type_="foreignkey",
    )
    op.drop_column("interview_sessions", "current_question_id")

