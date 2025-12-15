from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from typing import List, Optional

from app.models.audit_log import AuditLog


async def create_audit_log(
    db: AsyncSession,
    user_id: int,
    action: str,
    entity: str,
    entity_id: int = None,
    details: str = None,
) -> AuditLog:
    """
    Membuat audit log baru
    """
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        details=details,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


async def get_audit_logs(
    db: AsyncSession,
    user_id: Optional[int] = None,
    entity: Optional[str] = None,
    entity_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[AuditLog]:
    """
    Mendapatkan audit logs dengan filter
    """
    stmt = select(AuditLog)

    if user_id:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if entity:
        stmt = stmt.where(AuditLog.entity == entity)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)

    stmt = stmt.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
