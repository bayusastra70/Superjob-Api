# Central DB package init for Alembic.
# Keeps Base import and optional model discovery helpers.

import importlib
import os
import sys
from app.db.base import Base  # noqa: F401


def import_all_models() -> None:
    """
    Optionally import models from service packages so Alembic autogenerate
    can detect metadata. Safe no-op if packages are unavailable.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    services = ["superjob-talent-api", "superjob-corporate-api"]

    for service in services:
        service_path = os.path.join(base_dir, service)
        if os.path.exists(service_path) and service_path not in sys.path:
            sys.path.insert(0, service_path)

    for module_name in ("superjob_talent_api.app.models", "superjob_corporate_api.app.models"):
        try:
            importlib.import_module(module_name)
            print(f"Imported models from {module_name}", file=sys.stderr)
        except ImportError as exc:
            print(f"Warning: could not import {module_name}: {exc}", file=sys.stderr)
