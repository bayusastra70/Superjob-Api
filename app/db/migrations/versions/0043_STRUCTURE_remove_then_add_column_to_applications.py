from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0043'
down_revision = '0042'
branch_labels = None
depends_on = None


def upgrade():
    # Hapus kolom-kolom lama
    op.drop_column('applications', 'candidate_name')
    op.drop_column('applications', 'candidate_email')
    op.drop_column('applications', 'candidate_phone')
    op.drop_column('applications', 'candidate_linkedin')
    
    # Tambah kolom baru
    op.add_column('applications', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('applications', sa.Column('portofolio', sa.Text(), nullable=True))
    op.add_column('applications', sa.Column('coverletter', sa.Text(), nullable=True))


def downgrade():
    # Tambah kembali kolom-kolom lama
    op.add_column('applications', sa.Column('candidate_name', sa.String(255), nullable=True))
    op.add_column('applications', sa.Column('candidate_email', sa.String(255), nullable=True))
    op.add_column('applications', sa.Column('candidate_phone', sa.String(50), nullable=True))
    op.add_column('applications', sa.Column('candidate_linkedin', sa.String(255), nullable=True))
    
    # Hapus kolom baru
    op.drop_column('applications', 'address')
    op.drop_column('applications', 'portofolio')
    op.drop_column('applications', 'coverletter')