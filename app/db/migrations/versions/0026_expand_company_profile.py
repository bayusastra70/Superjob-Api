"""Expand company profile: add social links and consolidate attachments

Revision ID: 0026
Revises: 0025
Create Date: 2026-01-20 16:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0026'
down_revision = '0025'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add social media links to companies table
    op.add_column('companies', sa.Column('facebook_url', sa.String(length=255), nullable=True))
    op.add_column('companies', sa.Column('tiktok_url', sa.String(length=255), nullable=True))
    op.add_column('companies', sa.Column('youtube_url', sa.String(length=255), nullable=True))

    # 2. Create company_attachments table
    op.create_table(
        'company_attachments',
        sa.Column('company_id', sa.BigInteger(), primary_key=True),
        sa.Column('nib_url', sa.Text(), nullable=True),
        sa.Column('nib_storage_id', sa.String(length=255), nullable=True),
        sa.Column('npwp_url', sa.Text(), nullable=True),
        sa.Column('npwp_storage_id', sa.String(length=255), nullable=True),
        sa.Column('proposal_url', sa.Text(), nullable=True),
        sa.Column('proposal_storage_id', sa.String(length=255), nullable=True),
        sa.Column('portfolio_url', sa.Text(), nullable=True),
        sa.Column('portfolio_storage_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    )

    # 3. Data Migration: Copy NIB data from companies to company_attachments
    # Note: Using execute with raw SQL as it's a simple movement
    op.execute("""
        INSERT INTO company_attachments (company_id, nib_url, nib_storage_id)
        SELECT id, nib_document_url, nib_document_storage_id
        FROM companies
        WHERE nib_document_url IS NOT NULL
    """)

    # 4. Remove old columns from companies table
    op.drop_column('companies', 'nib_document_storage_id')
    op.drop_column('companies', 'nib_document_url')


def downgrade():
    # 1. Restore columns to companies table
    op.add_column('companies', sa.Column('nib_document_url', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('companies', sa.Column('nib_document_storage_id', sa.VARCHAR(length=255), autoincrement=False, nullable=True))

    # 2. Restore data
    op.execute("""
        UPDATE companies c
        SET nib_document_url = ca.nib_url,
            nib_document_storage_id = ca.nib_storage_id
        FROM company_attachments ca
        WHERE c.id = ca.company_id
    """)

    # 3. Drop company_attachments table
    op.drop_table('company_attachments')

    # 4. Remove social links
    op.drop_column('companies', 'youtube_url')
    op.drop_column('companies', 'tiktok_url')
    op.drop_column('companies', 'facebook_url')
