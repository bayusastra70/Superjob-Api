"""Create OJT (On-the-Job Training) tables

Revision ID: 0017
Revises: 0016
Create Date: 2026-02-12

Tabel baru:
- ojt_programs: Menyimpan daftar program OJT yang tersedia
- ojt_applications: Menyimpan pendaftaran talent ke program OJT
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0056"
down_revision = "0055"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =====================================================
    # TABEL 1: ojt_programs
    # Menyimpan informasi program OJT
    # Analoginya: ini seperti tabel "jobs" tapi untuk pelatihan
    # =====================================================
    op.create_table(
        "ojt_programs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("role", sa.String(100), nullable=True),          # Posisi yang dilatih (misal: Backend Developer)
        sa.Column("location", sa.String(255), nullable=True),      # Lokasi pelatihan
        sa.Column("duration_days", sa.Integer(), nullable=True),    # Durasi dalam hari
        sa.Column("trainer_id", sa.Integer(), nullable=True),       # FK ke users (siapa trainernya)
        sa.Column("max_participants", sa.Integer(), nullable=True), # Batas peserta
        sa.Column("requirements", sa.Text(), nullable=True),        # Syarat ikut
        sa.Column("skills", sa.JSON(), nullable=True),              # List skill yang diajarkan ["Python", "SQL"]
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),  # draft/published/ongoing/completed/archived
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        # Primary key
        sa.PrimaryKeyConstraint("id"),
        # Foreign key: trainer_id → users.id
        sa.ForeignKeyConstraint(["trainer_id"], ["users.id"], ondelete="SET NULL"),
    )

    # Index untuk mempercepat query yang sering dipakai
    op.create_index("ix_ojt_programs_status", "ojt_programs", ["status"])
    op.create_index("ix_ojt_programs_role", "ojt_programs", ["role"])
    op.create_index("ix_ojt_programs_location", "ojt_programs", ["location"])

    # =====================================================
    # TABEL 2: ojt_applications
    # Menyimpan pendaftaran talent ke program OJT
    # Analoginya: ini seperti tabel "applications" untuk job,
    # tapi khusus untuk OJT
    # =====================================================
    op.create_table(
        "ojt_applications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("talent_id", sa.Integer(), nullable=False),      # FK ke users (siapa yang daftar)
        sa.Column("program_id", sa.Integer(), nullable=False),     # FK ke ojt_programs (daftar ke program apa)
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),  # pending/screening/accepted/rejected/registered/withdrawn
        sa.Column("motivation_letter", sa.Text(), nullable=True),  # Surat motivasi (opsional)
        sa.Column("ai_fit_score", sa.Numeric(5, 2), nullable=True),  # Skor AI (future feature)
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),    # Kapan di-review
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=True),  # Kapan konfirmasi ikut
        # Primary key
        sa.PrimaryKeyConstraint("id"),
        # Foreign keys
        sa.ForeignKeyConstraint(["talent_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["program_id"], ["ojt_programs.id"], ondelete="CASCADE"),
        # Unique constraint: 1 talent hanya bisa daftar 1x ke program yang sama
        sa.UniqueConstraint("talent_id", "program_id", name="uq_ojt_app_talent_program"),
    )

    # Index untuk mempercepat query
    op.create_index("ix_ojt_applications_talent_id", "ojt_applications", ["talent_id"])
    op.create_index("ix_ojt_applications_program_id", "ojt_applications", ["program_id"])
    op.create_index("ix_ojt_applications_status", "ojt_applications", ["status"])


def downgrade() -> None:
    # Hapus tabel dalam urutan terbalik (karena ada FK dependency)
    op.drop_table("ojt_applications")
    op.drop_table("ojt_programs")
