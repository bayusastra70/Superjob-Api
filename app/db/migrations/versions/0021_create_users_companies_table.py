"""Create users_companies table

Revision ID: 0021
Revises: 0020
Create Date: 2026-01-12

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0021'
down_revision = '0020'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fix missing primary key on companies table if it doesn't exist
    bind = op.get_bind()
    res = bind.execute(sa.text("SELECT 1 FROM pg_constraint WHERE conname = 'companies_pkey'"))
    if not res.fetchone():
        # Check if id column exists (it should)
        op.create_primary_key('companies_pkey', 'companies', ['id'])

    op.create_table(
        'users_companies',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'company_id')
    )
    op.create_index('ix_users_companies_user_id', 'users_companies', ['user_id'])
    op.create_index('ix_users_companies_company_id', 'users_companies', ['company_id'])


def downgrade() -> None:
    op.drop_table('users_companies')
