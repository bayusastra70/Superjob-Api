"""add candidate_application, rejection_reasons, and audit_log tables

Revision ID: a1b2c3d4e5f6
Revises: 9c4f4c2f1d3b
Create Date: 2025-01-15 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '9c4f4c2f1d3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create rejection_reasons table first (referenced by candidate_application)
    op.create_table(
        'rejection_reasons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reason_code', sa.String(length=50), nullable=False),
        sa.Column('reason_text', sa.Text(), nullable=False),
        sa.Column('is_custom', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rejection_reasons_id', 'rejection_reasons', ['id'], unique=False)
    op.create_index('ix_rejection_reasons_reason_code', 'rejection_reasons', ['reason_code'], unique=True)
    
    # Create candidate_application table
    op.create_table(
        'candidate_application',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('applied_position', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('applied_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('rejection_reason_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['rejection_reason_id'], ['rejection_reasons.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_candidate_application_id', 'candidate_application', ['id'], unique=False)
    op.create_index('ix_candidate_application_email', 'candidate_application', ['email'], unique=True)
    
    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('entity', sa.String(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('details', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_log_id', 'audit_log', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_audit_log_id', table_name='audit_log')
    op.drop_table('audit_log')
    op.drop_index('ix_candidate_application_email', table_name='candidate_application')
    op.drop_index('ix_candidate_application_id', table_name='candidate_application')
    op.drop_table('candidate_application')
    op.drop_index('ix_rejection_reasons_reason_code', table_name='rejection_reasons')
    op.drop_index('ix_rejection_reasons_id', table_name='rejection_reasons')
    op.drop_table('rejection_reasons')

