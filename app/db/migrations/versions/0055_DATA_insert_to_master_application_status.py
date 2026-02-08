from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0055'
down_revision = '0054'
branch_labels = None
depends_on = None


def upgrade():
    # Insert data using raw SQL
    op.execute("""
        INSERT INTO master_application_status (name, code, description, display_order, created_at, updated_at) VALUES
        ('Applied', 'applied', 'Kandidat telah mengirim lamaran', 1, NOW(), NULL),
        ('Viewed', 'viewed', 'Lamaran telah dilihat oleh perekrut', 2, NOW(), NULL),
        ('Qualified', 'qualified', 'Kandidat memenuhi kualifikasi', 3, NOW(), NULL),
        ('AI Interview', 'ai_interview', 'Kandidat dipanggil untuk interview AI', 4, NOW(), NULL),
        ('Human Interview', 'human_interview', 'Kandidat dipanggil untuk interview', 5, NOW(), NULL),
        ('Contract Proposal', 'contract_proposal', 'Penawaran kontrak dikirim ke kandidat', 6, NOW(), NULL),
        ('Contract Signed', 'contract_signed', 'Kontrak telah ditandatangani', 7, NOW(), NULL),
        ('Not Qualified', 'not_qualified', 'Kandidat tidak memenuhi kualifikasi', 8, NOW(), NULL)
    """)


def downgrade():
    # Delete all inserted data
    op.execute("DELETE FROM master_application_status")