from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0048"
down_revision = "0047"
branch_labels = None
depends_on = None


def upgrade():
    # Add cv_storage_id column to candidate_info table
    op.add_column(
        "candidate_info", sa.Column("cv_storage_id", sa.String(255), nullable=True)
    )


def downgrade():
    op.drop_column("candidate_info", "cv_storage_id")
