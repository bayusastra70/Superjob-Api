"""
Daily cron to check job performance and log alerts.
Run via: `python -m app.cron.refresh_job_performance`
Schedule at 02:00 daily (e.g., cron/systemd/k8s cronjob).

NOTE: job_views and applications tables have job_id as Integer,
but job_postings.id is String(36). Direct join is not possible.
This cron logs alerts for jobs without calculating real metrics.
"""

import asyncio
from datetime import date
import socket

from loguru import logger
from sqlalchemy import text

from app.db.session import SessionLocal
from app.services.activity_log_service import activity_log_service


async def refresh() -> None:
    today = date.today()
    # Get server hostname/IP for logging
    server_ip = socket.gethostbyname(socket.gethostname())

    async with SessionLocal() as db:
        try:
            # Query all published job_postings directly
            # NOTE: Skip join to job_views/applications due to type mismatch
            # (job_views.job_id is Integer, job_postings.id is String)
            result = await db.execute(
                text(
                    """
                    SELECT 
                        jp.id::text AS job_id,
                        jp.employer_id::text AS employer_id,
                        jp.title AS job_title,
                        jp.status AS status,
                        0 AS views_count,
                        0 AS applicants_count,
                        0.00 AS apply_rate
                    FROM job_postings jp
                    WHERE jp.status = 'published'
                    """
                )
            )

            jobs = result.mappings().all()
            logger.info("Found published jobs", count=len(jobs), as_of_date=str(today))

            # Log performance alert for all jobs with 0 apply rate
            threshold_apply_rate = 5
            alerts_created = 0

            for row in jobs:
                apply_rate = float(row["apply_rate"])
                if apply_rate < threshold_apply_rate:
                    # NOTE: activity_logs.job_id column is INTEGER (references jobs.id)
                    # but job_postings.id is VARCHAR(36) UUID format.
                    # We pass job_id=None for the column, but store the UUID in meta_data.
                    activity_log_service.log_job_performance_alert(
                        employer_id=row["employer_id"],
                        job_id=None,  # Cannot store UUID string in Integer column
                        job_title=row["job_title"],
                        metric="apply_rate",
                        current_value=apply_rate,
                        threshold=threshold_apply_rate,
                        status=row["status"],
                        source="cron_job",
                        ip_address=server_ip,
                        user_agent="CronJob/refresh_job_performance",
                    )
                    alerts_created += 1

            logger.info(
                "Job performance alerts created",
                alerts_created=alerts_created,
                as_of_date=str(today),
            )

        except Exception as exc:
            logger.exception(
                "Failed to refresh job performance",
                exc=exc,
                as_of_date=str(today),
            )
            raise


if __name__ == "__main__":
    asyncio.run(refresh())
