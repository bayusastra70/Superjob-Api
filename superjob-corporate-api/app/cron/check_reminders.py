"""
Simple cron-friendly entrypoint to check pending reminders approaching their due time.
Intended to be scheduled (e.g., via cron, systemd timer, or a containerized job).
"""
import asyncio
import sys

from loguru import logger

from app.db.session import SessionLocal
from app.services.reminder_service import get_pending_due_reminders
from app.services.socketio_emitter import emit_reminder_due


async def main() -> None:
    try:
        async with SessionLocal() as db:
            reminders = await get_pending_due_reminders(db)
    except Exception:
        logger.exception("Failed to fetch pending reminders")
        sys.exit(1)

    for reminder in reminders:
        try:
            await emit_reminder_due(reminder)
        except Exception:
            # Continue processing other reminders even if one emit fails.
            logger.exception(
                "Skipping reminder after emit failure",
                reminder_id=str(reminder.id),
            )
            continue

        logger.info(
            "Reminder nearing deadline",
            reminder_id=str(reminder.id),
            employer_id=str(reminder.employer_id),
            due_at=str(reminder.due_at),
            task_type=reminder.task_type.value,
        )

    logger.info("Cron check completed", processed=len(reminders))


if __name__ == "__main__":
    asyncio.run(main())
