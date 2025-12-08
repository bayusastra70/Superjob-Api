import socketio
from loguru import logger

from app.core.config import settings
from app.models.reminder import ReminderTask


async def _emit(event: str, payload: dict) -> None:
    sio = socketio.AsyncClient()
    try:
        await sio.connect(
            settings.socketio_endpoint,
            namespaces=[settings.socketio_namespace],
            wait_timeout=5,
        )
        await sio.emit(event, payload, namespace=settings.socketio_namespace)
        logger.info(
            "Emitted Socket.IO event",
            event=event,
            namespace=settings.socketio_namespace,
            endpoint=settings.socketio_endpoint,
        )
    except Exception as exc:
        logger.exception(
            "Failed to emit Socket.IO event",
            exc=exc,
            event=event,
            namespace=settings.socketio_namespace,
            endpoint=settings.socketio_endpoint,
        )
        raise
    finally:
        if sio.connected:
            await sio.disconnect()


def _serialize_reminder(reminder: ReminderTask) -> dict:
    return {
        "id": str(reminder.id),
        "employer_id": str(reminder.employer_id),
        "job_id": str(reminder.job_id) if reminder.job_id else None,
        "candidate_id": str(reminder.candidate_id) if reminder.candidate_id else None,
        "task_title": reminder.task_title,
        "task_type": reminder.task_type.value,
        "redirect_url": reminder.redirect_url,
        "due_at": reminder.due_at.isoformat() if reminder.due_at else None,
        "status": reminder.status.value,
    }


async def emit_reminder_created(reminder: ReminderTask) -> None:
    await _emit("reminder_created", _serialize_reminder(reminder))


async def emit_reminder_updated(reminder: ReminderTask) -> None:
    await _emit("reminder_updated", _serialize_reminder(reminder))


async def emit_reminder_due(reminder: ReminderTask) -> None:
    await _emit("reminder_due", _serialize_reminder(reminder))
