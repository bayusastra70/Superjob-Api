from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0047"
down_revision = "0046"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "candidate_info",
        sa.Column(
            "preferred_locations", postgresql.ARRAY(sa.String(100)), nullable=True
        ),
    )
    op.add_column(
        "candidate_info",
        sa.Column(
            "preferred_work_modes", postgresql.ARRAY(sa.String(20)), nullable=True
        ),
    )
    op.add_column(
        "candidate_info",
        sa.Column(
            "preferred_job_types", postgresql.ARRAY(sa.String(50)), nullable=True
        ),
    )
    op.add_column(
        "candidate_info",
        sa.Column("expected_salary_min", sa.Numeric(12, 2), nullable=True),
    )
    op.add_column(
        "candidate_info",
        sa.Column("expected_salary_max", sa.Numeric(12, 2), nullable=True),
    )
    op.add_column(
        "candidate_info",
        sa.Column("salary_currency", sa.String(8), nullable=True, server_default="IDR"),
    )
    op.add_column(
        "candidate_info",
        sa.Column(
            "preferred_industries", postgresql.ARRAY(sa.String(100)), nullable=True
        ),
    )
    op.add_column(
        "candidate_info",
        sa.Column(
            "preferred_divisions", postgresql.ARRAY(sa.String(100)), nullable=True
        ),
    )
    op.add_column(
        "candidate_info",
        sa.Column(
            "auto_apply_enabled", sa.Boolean(), nullable=True, server_default="false"
        ),
    )


def downgrade():
    op.drop_column("candidate_info", "auto_apply_enabled")
    op.drop_column("candidate_info", "preferred_divisions")
    op.drop_column("candidate_info", "preferred_industries")
    op.drop_column("candidate_info", "salary_currency")
    op.drop_column("candidate_info", "expected_salary_max")
    op.drop_column("candidate_info", "expected_salary_min")
    op.drop_column("candidate_info", "preferred_job_types")
    op.drop_column("candidate_info", "preferred_work_modes")
    op.drop_column("candidate_info", "preferred_locations")
