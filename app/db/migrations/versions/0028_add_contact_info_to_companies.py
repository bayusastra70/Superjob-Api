"""Add email and phone to companies table

Revision ID: 0028
Revises: 0027
Create Date: 2026-01-21 14:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0028'
down_revision = '0027'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add email and phone columns to companies table
    op.add_column('companies', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('companies', sa.Column('phone', sa.String(length=255), nullable=True))

    # 2. Data Migration: Populate from Admin user (default_role_id = 1)
    op.execute("""
        UPDATE companies c
        SET email = u.email,
            phone = u.phone
        FROM users_companies uc
        JOIN users u ON uc.user_id = u.id
        WHERE c.id = uc.company_id
          AND u.default_role_id = 1
    """)


def downgrade():
    # Remove email and phone columns
    op.drop_column('companies', 'phone')
    op.drop_column('companies', 'email')
