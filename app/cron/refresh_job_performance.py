"""
Daily cron to check job performance and log alerts.
Run via: `python -m app.cron.refresh_job_performance`
Schedule at 02:00 daily (e.g., cron/systemd/k8s cronjob).

NOTE: After migration 0012, jobs table has Integer IDs.
This cron now uses the unified jobs table.
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
            # Query all published jobs from the unified jobs table
            result = await db.execute(
                text(
                    """
                    SELECT 
                        j.id AS job_id,
                        j.employer_id AS employer_id,
                        j.title AS job_title,
                        j.status::text AS status,
                        COALESCE((SELECT COUNT(*) FROM job_views jv WHERE jv.job_id = j.id), 0) AS views_count,
                        COALESCE((SELECT COUNT(*) FROM applications a WHERE a.job_id = j.id), 0) AS applicants_count,
                        CASE 
                            WHEN COALESCE((SELECT COUNT(*) FROM job_views jv WHERE jv.job_id = j.id), 0) = 0 THEN 0.00
                            ELSE ROUND(
                                (COALESCE((SELECT COUNT(*) FROM applications a WHERE a.job_id = j.id), 0)::numeric / 
                                 COALESCE((SELECT COUNT(*) FROM job_views jv WHERE jv.job_id = j.id), 1)::numeric) * 100, 2
                            )
                        END AS apply_rate
                    FROM jobs j
                    WHERE j.status = 'published'
                    """
                )
            )

            jobs = result.mappings().all()
            logger.info("Found published jobs", count=len(jobs), as_of_date=str(today))

            # Log performance alert for jobs with low apply rate
            threshold_apply_rate = 5
            alerts_created = 0

            for row in jobs:
                apply_rate = float(row["apply_rate"])
                if apply_rate < threshold_apply_rate:
                    # Now job_id is Integer, can store directly
                    activity_log_service.log_job_performance_alert(
                        employer_id=row["employer_id"],
                        job_id=row["job_id"],  # Integer now
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
