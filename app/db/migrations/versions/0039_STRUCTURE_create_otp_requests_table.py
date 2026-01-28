from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision = '0039'
down_revision = '0038'


def upgrade() -> None:
    op.create_table(
        'otp_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('otp_code', sa.String(length=255), nullable=False),
        sa.Column('is_used', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_otp_requests_email'), 'otp_requests', ['email'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_otp_requests_email'), table_name='otp_requests')
    op.drop_table('otp_requests')
