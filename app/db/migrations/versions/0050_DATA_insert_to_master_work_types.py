from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0050"
down_revision = "0049"
branch_labels = None
depends_on = None


def upgrade():
    # Insert initial data into master_work_types
    # Karena tidak ada UNIQUE constraint, kita gunakan approach yang lebih aman
    conn = op.get_bind()
    
    # Data yang akan di-insert
    work_types = [
        ('Remote', 'remote', 'Fully remote work'),
        ('Hybrid', 'hybrid', 'Hybrid work arrangement'),
        ('On-site', 'onsite', 'On-site work only'),
    ]
    
    # Insert data satu per satu dengan cek manual
    for name, code, description in work_types:
        # Cek apakah data dengan code yang sama sudah ada
        result = conn.execute(
            sa.text("SELECT id FROM master_work_types WHERE code = :code"),
            {"code": code}
        ).fetchone()
        
        # Jika belum ada, insert
        if not result:
            conn.execute(
                sa.text("""
                    INSERT INTO master_work_types (name, code, description) 
                    VALUES (:name, :code, :description)
                """),
                {"name": name, "code": code, "description": description}
            )


def downgrade():
    # Hapus data yang di-insert berdasarkan code
    op.execute("""
        DELETE FROM master_work_types 
        WHERE code IN (
            'remote'
            , 'hybrid'
            , 'onsite'
        );
    """)