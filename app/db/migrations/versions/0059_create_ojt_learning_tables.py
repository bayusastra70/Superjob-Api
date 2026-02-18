"""create_ojt_learning_tables

Revision ID: 0059
Revises: 0058
Create Date: 2026-02-18

Membuat 4 tabel utama untuk fitur Learning Experience OJT:
1. ojt_agendas (Jadwal sesi pelatihan)
2. ojt_attendance (Kehadiran peserta)
3. ojt_tasks (Tugas OJT)
4. ojt_task_submissions (Pengumpulan tugas)

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '0059'
down_revision = '0058'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Tabel ojt_agendas
    op.create_table(
        'ojt_agendas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('session_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True), # Durasi sesi (menit)
        sa.Column('location', sa.String(255), nullable=True),       # Link meet / Nama ruangan
        sa.Column('meeting_link', sa.Text(), nullable=True),        # URL meeting (Zoom/GMeet)
        sa.Column('trainer_id', sa.Integer(), nullable=True),       # Trainer sesi ini
        sa.Column('order_number', sa.Integer(), default=0),         # Urutan sesi
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['program_id'], ['ojt_programs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['trainer_id'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_ojt_agendas_program_id', 'ojt_agendas', ['program_id'])

    # 2. Tabel ojt_attendance (Absensi)
    op.create_table(
        'ojt_attendance',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('agenda_id', sa.Integer(), nullable=False),
        sa.Column('talent_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='present'), # present, absent, excused
        sa.Column('checked_in_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agenda_id'], ['ojt_agendas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['talent_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('agenda_id', 'talent_id', name='uq_agenda_talent_attendance') # 1 talent 1 absen per sesi
    )
    op.create_index('ix_ojt_attendance_agenda_id', 'ojt_attendance', ['agenda_id'])
    op.create_index('ix_ojt_attendance_talent_id', 'ojt_attendance', ['talent_id'])

    # 3. Tabel ojt_tasks (Tugas)
    op.create_table(
        'ojt_tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_score', sa.Integer(), default=100),
        sa.Column('order_number', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['program_id'], ['ojt_programs.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_ojt_tasks_program_id', 'ojt_tasks', ['program_id'])

    # 4. Tabel ojt_task_submissions (Pengumpulan Tugas)
    op.create_table(
        'ojt_task_submissions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('talent_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),             # Jawaban teks
        sa.Column('file_url', sa.String(500), nullable=True),       # Link file (jika ada)
        sa.Column('status', sa.String(20), server_default='submitted'), # submitted, graded, late
        sa.Column('score', sa.Float(), nullable=True),              # Nilai (0-100)
        sa.Column('feedback', sa.Text(), nullable=True),            # Masukan dari trainer
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('graded_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['task_id'], ['ojt_tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['talent_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('task_id', 'talent_id', name='uq_task_talent_submission') # 1 talent 1 jawaban per tugas
    )
    op.create_index('ix_ojt_task_submissions_task_id', 'ojt_task_submissions', ['task_id'])
    op.create_index('ix_ojt_task_submissions_talent_id', 'ojt_task_submissions', ['talent_id'])


def downgrade() -> None:
    op.drop_table('ojt_task_submissions')
    op.drop_table('ojt_tasks')
    op.drop_table('ojt_attendance')
    op.drop_table('ojt_agendas')
