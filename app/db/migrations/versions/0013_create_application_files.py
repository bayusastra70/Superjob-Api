from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create application_files table
    op.create_table(
        "application_files",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("file_type", sa.String(50), nullable=True, server_default="resume"),  # <-- TAMBAHKAN INI
        sa.Column("stored_filename", sa.String(255), nullable=True),  # <-- TAMBAHKAN INI
        sa.Column("upload_status", sa.String(20), nullable=True),
        sa.Column("upload_process_time", sa.Integer(), nullable=True),  # in milliseconds
        sa.Column("file_url", sa.Text(), nullable=True),  # Full URL to stored file
        sa.Column("created_by", sa.Integer(), nullable=True),  # <-- TAMBAHKAN INI
        sa.Column("uploader_ip", sa.String(50), nullable=True),  # <-- TAMBAHKAN INI (opsional)
        sa.Column("uploader_user_agent", sa.Text(), nullable=True),  # <-- TAMBAHKAN INI (opsional)
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["application_id"],
            ["applications.id"],
            ondelete="CASCADE",  # Delete files when application is deleted
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.Index("idx_application_files_application_id", "application_id"),
    )

def downgrade() -> None:
    # Drop table
    op.drop_table("application_files")