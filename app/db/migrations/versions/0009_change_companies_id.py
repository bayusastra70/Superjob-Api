"""Change companies.id from UUID to BIGSERIAL

Revision ID: 0002_change_companies_id_bigserial
Revises: 0001_initial_database
Create Date: 2025-01-05
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade():
    # ============================
    # 1. DROP FOREIGN KEY
    # ============================
    op.drop_constraint(
        "company_reviews_company_id_fkey",
        "company_reviews",
        type_="foreignkey",
    )

    # ============================
    # 2. DROP PRIMARY KEY
    # ============================
    op.drop_constraint(
        "companies_pkey",
        "companies",
        type_="primary",
    )

    # ============================
    # 3. DROP OLD UUID COLUMN
    # ============================
    op.drop_column("companies", "id")

    # ============================
    # 4. ADD NEW BIGSERIAL COLUMN
    # ============================
    op.add_column(
        "companies",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
            nullable=False,
        ),
    )

    # ============================
    # 5. RECREATE INDEX
    # ============================
    op.create_index(
        "ix_companies_id",
        "companies",
        ["id"],
        unique=False,
    )


def downgrade():
    # ============================
    # 1. DROP INDEX
    # ============================
    op.drop_index("ix_companies_id", table_name="companies")

    # ============================
    # 2. DROP BIGSERIAL COLUMN
    # ============================
    op.drop_column("companies", "id")

    # ============================
    # 3. RESTORE UUID COLUMN
    # ============================
    op.add_column(
        "companies",
        sa.Column(
            "id",
            sa.String(length=36),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
    )

    # ============================
    # 4. RESTORE PRIMARY KEY
    # ============================
    op.create_primary_key("companies_pkey", "companies", ["id"])

    # ============================
    # 5. RESTORE FOREIGN KEY
    # ============================
    op.create_foreign_key(
        "company_reviews_company_id_fkey",
        "company_reviews",
        "companies",
        ["company_id"],
        ["id"],
        ondelete="CASCADE",
    )
