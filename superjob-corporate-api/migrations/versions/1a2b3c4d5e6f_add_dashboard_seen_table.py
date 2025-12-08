"""add dashboard_seen table"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "1a2b3c4d5e6f"
down_revision = "9c4f4c2f1d3b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dashboard_seen",
        sa.Column("employer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_key", sa.String(length=50), nullable=False),
        sa.Column("seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("employer_id", "item_key"),
    )


def downgrade() -> None:
    op.drop_table("dashboard_seen")
