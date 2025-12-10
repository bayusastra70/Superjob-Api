# superjob-db-migrations/app/db/__init__.py

import os
import sys
from app.db.base import Base

def import_all_models():
    """Import semua model dari semua services"""
    # Tambahkan path ke semua services
    services = ['superjob-talent-api', 'superjob-corporate-api']
    
    for service in services:
        service_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', service)
        if os.path.exists(service_path):
            sys.path.insert(0, service_path)
    
    # Import model dari talent-api
    try:
        from superjob_talent_api.app.models import Company, CompanyReview, User
        print(f"✓ Imported models from talent-api")
    except ImportError as e:
        print(f"✗ Could not import models from talent-api: {e}")
    
    # Import model dari corporate-api
    try:
        from superjob_corporate_api.app.models import *  # Import semua model
        print(f"✓ Imported models from corporate-api")
    except ImportError as e:
        print(f"✗ Could not import models from corporate-api: {e}")