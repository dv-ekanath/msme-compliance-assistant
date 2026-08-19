from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_audit_event(
    db: Session,
    *,
    actor_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    detail: str,
) -> None:
    """Appends an AuditLog row via db.add() only -- the caller's existing
    db.commit() persists it. Never call db.commit() here: doing so would
    commit the caller's other pending changes early, out of order with
    the rest of that route's transaction.
    """
    db.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            detail=detail,
        )
    )
