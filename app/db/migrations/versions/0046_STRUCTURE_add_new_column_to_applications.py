from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0046"
down_revision = "0045"
branch_labels = None
depends_on = None


def upgrade():
    # Menambahkan kolom candidate_name dengan tipe data VARCHAR
    op.add_column(
        "applications",
        sa.Column("candidate_name", sa.String(length=255), nullable=True),
    )
    
    # Menambahkan kolom candidate_wa_number dengan tipe data VARCHAR
    op.add_column(
        "applications",
        sa.Column("candidate_wa_number", sa.String(length=50), nullable=True),
    )
    
    # Optional: Membuat index untuk pencarian yang lebih cepat
    # op.create_index(op.f('ix_applications_candidate_name'), 'applications', ['candidate_name'])
    # op.create_index(op.f('ix_applications_candidate_wa_number'), 'applications', ['candidate_wa_number'])


def downgrade():
    # Menghapus index jika dibuat
    # op.drop_index(op.f('ix_applications_candidate_wa_number'), table_name='applications')
    # op.drop_index(op.f('ix_applications_candidate_name'), table_name='applications')
    
    # Menghapus kolom candidate_wa_number
    op.drop_column("applications", "candidate_wa_number")
    
    # Menghapus kolom candidate_name
    op.drop_column("applications", "candidate_name")