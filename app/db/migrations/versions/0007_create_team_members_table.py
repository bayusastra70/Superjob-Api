"""Create team_members table

Revision ID: 0007
Revises: 0006
Create Date: 2024-12-17
"""

from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type
    # op.execute(
    #     "CREATE TYPE team_member_role AS ENUM ('admin', 'hr_manager', 'recruiter', 'hiring_manager', 'viewer')"
    # )

    # Create table (Normalized Version)
    op.create_table(
        "team_members",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("employer_id", sa.Integer(), nullable=False),
        # user_id sekarang wajib (nullable=False) karena name & email diambil dari tabel users
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "admin",
                "hr_manager",
                "recruiter",
                "hiring_manager",
                "viewer",
                name="team_member_role",
            ),
            nullable=False,
            server_default="viewer",
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # Create indexes
    op.create_index("ix_team_members_employer_id", "team_members", ["employer_id"])
    op.create_index("ix_team_members_user_id", "team_members", ["user_id"])


def downgrade() -> None:
    op.drop_table("team_members")
    op.execute("DROP TYPE team_member_role")
