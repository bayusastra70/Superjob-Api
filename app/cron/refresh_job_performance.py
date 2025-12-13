"""
Daily cron to precompute job performance metrics into job_performance_daily.
Run via: `python -m app.cron.refresh_job_performance`
Schedule at 02:00 daily (e.g., cron/systemd/k8s cronjob).
"""
import asyncio
from datetime import date

from loguru import logger
from sqlalchemy import text

from app.db.session import SessionLocal
from app.services.activity_log_service import activity_log_service


async def refresh() -> None:
    today = date.today()
    async with SessionLocal() as db:
        try:
            # Clear today's aggregates to avoid duplicates
            await db.execute(
                text("DELETE FROM job_performance_daily WHERE as_of_date = :as_of_date"),
                {"as_of_date": today},
            )

            # Insert aggregated metrics
            await db.execute(
                text(
                    """
                    WITH views AS (
                        SELECT job_id, COUNT(*)::bigint AS views_count
                        FROM job_views
                        GROUP BY job_id
                    ),
                    apps AS (
                        SELECT job_id, COUNT(*)::bigint AS applicants_count
                        FROM applications
                        GROUP BY job_id
                    )
                    INSERT INTO job_performance_daily (
                        job_id, as_of_date, employer_id, job_title,
                        views_count, applicants_count, apply_rate, status
                    )
                    SELECT
                        jp.id,
                        :as_of_date,
                        jp.employer_id,
                        COALESCE(jp.title, ''),
                        COALESCE(v.views_count, 0),
                        COALESCE(a.applicants_count, 0),
                        CASE
                            WHEN COALESCE(v.views_count, 0) = 0 THEN 0
                            ELSE ROUND((COALESCE(a.applicants_count,0)::numeric / NULLIF(v.views_count,0)) * 100, 2)
                        END,
                        jp.status
                    FROM job_postings jp
                    LEFT JOIN views v ON v.job_id::text = jp.id::text
                    LEFT JOIN apps a ON a.job_id::text = jp.id::text;
                    """
                ),
                {"as_of_date": today},
            )

            await db.commit()
            logger.info("Job performance daily refreshed", as_of_date=str(today))

            threshold_apply_rate = 5
            low_perf = await db.execute(
                text(
                    """
                    SELECT employer_id::text AS employer_id,
                           job_id::text AS job_id,
                           job_title,
                           apply_rate,
                           status,
                           applicants_count
                    FROM job_performance_daily
                    WHERE as_of_date = :as_of_date
                      AND apply_rate < :threshold
                    """
                ),
                {"as_of_date": today, "threshold": threshold_apply_rate},
            )
            for row in low_perf.mappings().all():
                activity_log_service.log_job_performance_alert(
                    employer_id=row["employer_id"],
                    job_id=row["job_id"],
                    job_title=row["job_title"],
                    metric="apply_rate",
                    current_value=float(row["apply_rate"]),
                    threshold=threshold_apply_rate,
                    status=row["status"],
                )
        except Exception as exc:
            await db.rollback()
            logger.exception("Failed to refresh job performance daily", exc=exc, as_of_date=str(today))
            raise


if __name__ == "__main__":
    asyncio.run(refresh())
