from datetime import datetime
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers
revision = '0032'
down_revision = '0031'
branch_labels = None
depends_on = None

def upgrade():
    # Hanya insert user 8 dan 1 yang kemungkinan besar ada
    op.execute("""
        INSERT INTO users_companies (user_id, company_id)
        VALUES 
        (8, 1),
        (1, 1)
        ON CONFLICT (user_id, company_id) DO NOTHING
    """)

def downgrade():
    # Method 1: Gunakan op.execute() langsung
    op.execute("""
        DELETE FROM users_companies 
        WHERE user_id IN (8, 1) 
        AND company_id = 1
    """)