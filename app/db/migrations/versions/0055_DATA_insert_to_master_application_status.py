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
        INSERT INTO master_application_status (name, code, description, created_at, updated_at) VALUES
        ('Applied', 'applied', 'Kandidat telah mengirim lamaran', NOW(), NULL),
        ('Viewed', 'viewed', 'Lamaran telah dilihat oleh perekrut', NOW(), NULL),
        ('In Review', 'in_review', 'Lamaran sedang dalam proses review', NOW(), NULL),
        ('Interview', 'interview', 'Kandidat dipanggil untuk interview', NOW(), NULL),
        ('Qualified', 'qualified', 'Kandidat memenuhi kualifikasi', NOW(), NULL),
        ('Not Qualified', 'not_qualified', 'Kandidat tidak memenuhi kualifikasi', NOW(), NULL),
        ('Contract Proposal', 'contract_proposal', 'Penawaran kontrak dikirim ke kandidat', NOW(), NULL),
        ('Contract Signed', 'contract_signed', 'Kontrak telah ditandatangani', NOW(), NULL)
    """)


def downgrade():
    # Delete all inserted data
    op.execute("DELETE FROM master_application_status")