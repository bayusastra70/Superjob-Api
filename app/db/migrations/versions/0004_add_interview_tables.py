"""Add interview tables

Revision ID: 0004_add_interview_tables
Revises: 0003_cleanup_role_redundancy
Create Date: 2025-12-16 04:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0004_add_interview_tables'
down_revision = '0003_cleanup_role_redundancy'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create interview_sessions table
    op.create_table(
        'interview_sessions',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('position', sa.String(length=255), nullable=False),
        sa.Column('level', sa.String(length=50), nullable=False),
        sa.Column('total_questions', sa.Integer(), nullable=False),
        sa.Column('interview_type', sa.String(length=50), nullable=False),
        sa.Column('question_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_question_index', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_interview_sessions_id', 'interview_sessions', ['id'], unique=False)
    op.create_index('ix_interview_sessions_user_id', 'interview_sessions', ['user_id'], unique=False)
    op.create_index('ix_interview_sessions_status', 'interview_sessions', ['status'], unique=False)
    
    # Create interview_messages table
    op.create_table(
        'interview_messages',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('sender', sa.String(length=10), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_interview_messages_id', 'interview_messages', ['id'], unique=False)
    op.create_index('ix_interview_messages_session_id', 'interview_messages', ['session_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_interview_messages_session_id', table_name='interview_messages')
    op.drop_index('ix_interview_messages_id', table_name='interview_messages')
    op.drop_table('interview_messages')
    op.drop_index('ix_interview_sessions_status', table_name='interview_sessions')
    op.drop_index('ix_interview_sessions_user_id', table_name='interview_sessions')
    op.drop_index('ix_interview_sessions_id', table_name='interview_sessions')
    op.drop_table('interview_sessions')

