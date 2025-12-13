"""add activity_logs table for notification/log activity feed"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "4d5e6f7a8b9c"
down_revision = "2b3c4d5e6f70"
branch_labels = None
depends_on = None


def upgrade() -> None:
    activity_type = postgresql.ENUM(
        "new_applicant",
        "status_update",
        "new_message",
        "job_performance_alert",
        "system_event",
        name="activity_type",
    )
    activity_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "activity_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("employer_id", sa.String(length=64), nullable=False),
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
        sa.Column("meta_data", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("job_id", sa.String(length=64), nullable=True),
        sa.Column("applicant_id", sa.Integer(), nullable=True),
        sa.Column("message_id", sa.String(length=64), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.create_index("ix_activity_logs_employer", "activity_logs", ["employer_id"])
    op.create_index("ix_activity_logs_type", "activity_logs", ["type"])
    op.create_index("ix_activity_logs_is_read", "activity_logs", ["is_read"])
    op.create_index("ix_activity_logs_job_id", "activity_logs", ["job_id"])
    op.create_index("ix_activity_logs_applicant_id", "activity_logs", ["applicant_id"])
    op.create_index("ix_activity_logs_message_id", "activity_logs", ["message_id"])
    op.create_index(
        "ix_activity_logs_timestamp_desc",
        "activity_logs",
        ["timestamp"],
        postgresql_using="btree",
    )


def downgrade() -> None:
    op.drop_index("ix_activity_logs_timestamp_desc", table_name="activity_logs")
    op.drop_index("ix_activity_logs_message_id", table_name="activity_logs")
    op.drop_index("ix_activity_logs_applicant_id", table_name="activity_logs")
    op.drop_index("ix_activity_logs_job_id", table_name="activity_logs")
    op.drop_index("ix_activity_logs_is_read", table_name="activity_logs")
    op.drop_index("ix_activity_logs_type", table_name="activity_logs")
    op.drop_index("ix_activity_logs_employer", table_name="activity_logs")
    op.drop_table("activity_logs")
    op.execute("DROP TYPE IF EXISTS activity_type")
