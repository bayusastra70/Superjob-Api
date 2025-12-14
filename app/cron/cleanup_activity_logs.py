"""
Cron utility to delete activity logs older than 14 days.
Run via: `python -m app.cron.cleanup_activity_logs`
Schedule daily (e.g., 03:00) via cron/systemd/k8s cronjob.
"""
import asyncio
from loguru import logger

from app.services.activity_log_service import activity_log_service


async def cleanup(days: int = 14) -> None:
    deleted = activity_log_service.purge_older_than(days)
    logger.info("Cleanup completed", deleted=deleted, days=days)


if __name__ == "__main__":
    asyncio.run(cleanup())
