"""Create users_companies table

Revision ID: 0021
Revises: 0020
Create Date: 2026-01-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '0021'
down_revision = '0020'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # 1. Check if 'companies' table has a Primary Key
    pk_constraint = inspector.get_pk_constraint('companies')
    
    # If no columns are returned in constrained_columns, PK is missing
    if not pk_constraint.get('constrained_columns'):
        op.create_primary_key('companies_pkey', 'companies', ['id'])
    
    # 2. Check for Type Mismatch (Optional but recommended)
    # Ensure companies.id is actually a BigInteger to match your new table
    columns = inspector.get_columns('companies')
    id_column = next((col for col in columns if col['name'] == 'id'), None)

    if id_column:
        # If companies.id is not BIGINT, alter it to match users_companies
        if not isinstance(id_column['type'], sa.BigInteger):
            op.alter_column('companies', 'id', type_=sa.BigInteger())

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
