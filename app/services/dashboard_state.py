import uuid
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

VALID_ITEMS = {"newApplicants", "newMessages", "newJobPosts"}


async def mark_seen_items(db: AsyncSession, employer_id: uuid.UUID, items: Iterable[str]) -> None:
    now = datetime.now(timezone.utc)

    to_update = [i for i in items if i in VALID_ITEMS]
    if not to_update:
        return

    # Simple upsert into a generic key-value table; if table missing, no-op.
    for item in to_update:
        try:
            await db.execute(
                text(
                    """
                    INSERT INTO dashboard_seen (employer_id, item_key, seen_at)
                    VALUES (:employer_id, :item_key, :seen_at)
                    ON CONFLICT (employer_id, item_key) DO UPDATE
                    SET seen_at = EXCLUDED.seen_at
                    """
                ),
                {"employer_id": str(employer_id), "item_key": item, "seen_at": now},
            )
        except Exception:
            # If table not present, skip; keeps endpoint graceful.
            pass
    await db.commit()


async def reset_badges(db: AsyncSession, employer_id: uuid.UUID, items: Iterable[str]) -> None:
    to_reset = [i for i in items if i in VALID_ITEMS]
    if not to_reset:
        return

    for item in to_reset:
        try:
            await db.execute(
                text(
                    """
                    INSERT INTO dashboard_seen (employer_id, item_key, seen_at)
                    VALUES (:employer_id, :item_key, :seen_at)
                    ON CONFLICT (employer_id, item_key) DO UPDATE
                    SET seen_at = :seen_at
                    """
                ),
                {
                    "employer_id": str(employer_id),
                    "item_key": item,
                    "seen_at": datetime.now(timezone.utc),
                },
            )
        except Exception:
            pass

    await db.commit()
