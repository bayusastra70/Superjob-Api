"""Add company_id column to ojt_programs

Revision ID: 0058
Revises: 0057
Create Date: 2026-02-17

Menambahkan kolom company_id ke tabel ojt_programs
agar bisa menampilkan profil company di OJT list dan detail.
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0058"
down_revision = "0057"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ojt_programs",
        sa.Column(
            "company_id",
            sa.BigInteger(),
            nullable=True,
            comment="FK ke companies.id - perusahaan penyelenggara OJT",
        ),
    )
    op.create_index("ix_ojt_programs_company_id", "ojt_programs", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_ojt_programs_company_id", table_name="ojt_programs")
    op.drop_column("ojt_programs", "company_id")
