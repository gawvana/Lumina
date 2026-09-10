"""Audit log service for recording immutable audit trail."""

import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.audit import AuditLog


async def record_audit(
    db: AsyncSession,
    school_id: str,
    entity_type: str,
    entity_id: str,
    action: str,
    user_id: Optional[str] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """Inserts an immutable audit record into audit_logs table."""
    audit_entry = AuditLog(
        id=str(uuid.uuid4()),
        school_id=school_id,
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        old_values=old_values,
        new_values=new_values,
        reason=reason,
        ip_address=ip_address,
    )
    db.add(audit_entry)
    await db.flush()
    return audit_entry
