from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domain.enums import FilingStatus
from app.models.business import Business
from app.models.filing import Filing
from app.models.obligation import Obligation
from app.models.user import User
from app.services.audit import log_audit_event


class FilingStateError(Exception):
    """A requested state transition isn't valid from the Filing's current
    status. Routes translate this into a 409 -- kept as a plain exception
    here (not an HTTPException) so this module stays framework-free and
    unit-testable on its own.
    """


def generate_draft_document(obligation: Obligation, business: Business, period: str | None) -> str:
    """Deterministic template, not LLM-generated -- CLAUDE.md rule 4: the
    LLM's job is explaining/citing, never deciding what's in the record
    of a legal filing. Reproducible across runs, so it's testable and
    doesn't need a live LLM call on a route whose entire premise is
    "nothing here is fuzzy."
    """
    period_label = period or "the current period"
    due_label = obligation.due_date.isoformat() if obligation.due_date else "no fixed due date"
    return (
        f"DRAFT FILING -- {obligation.title}\n"
        f"Business: {business.name}"
        f"{f' (GSTIN {business.gstin})' if business.gstin else ''}\n"
        f"Regulation: {obligation.regulation_title} ({obligation.regulation.authority})\n"
        f"Source: {obligation.regulation_source_url}\n"
        f"Period: {period_label}\n"
        f"Due date: {due_label}\n"
        f"Reason applicable: {obligation.reason}\n"
        "\n"
        "This draft was generated deterministically from the business's Digital "
        "Twin -- no AI/LLM decided any of its content. It requires human review "
        "and approval before submission; the eventual submission is a simulated "
        "mock, not a real filing with any government portal."
    )


def create_filing(db: Session, *, obligation: Obligation, actor: User, period: str | None) -> Filing:
    existing = (
        db.query(Filing)
        .filter(Filing.obligation_id == obligation.id, Filing.period == period, Filing.status == FilingStatus.DRAFT)
        .first()
    )
    if existing is not None:
        raise FilingStateError("A draft filing already exists for this obligation and period.")

    filing = Filing(
        obligation_id=obligation.id,
        period=period,
        status=FilingStatus.DRAFT,
        document_ref=generate_draft_document(obligation, obligation.business, period),
    )
    db.add(filing)
    db.flush()

    log_audit_event(
        db,
        actor_id=actor.id,
        action="filing.created",
        entity_type="filing",
        entity_id=filing.id,
        detail=f"{actor.email} prepared a draft filing for '{obligation.title}'.",
    )
    db.commit()
    db.refresh(filing)
    return filing


def approve_filing(db: Session, *, filing: Filing, actor: User) -> Filing:
    if filing.status != FilingStatus.DRAFT:
        raise FilingStateError(f"Filing is '{filing.status.value}', not 'draft' -- cannot approve.")

    filing.status = FilingStatus.APPROVED
    filing.human_approved_by = actor.id

    log_audit_event(
        db,
        actor_id=actor.id,
        action="filing.approved",
        entity_type="filing",
        entity_id=filing.id,
        detail=f"{actor.email} approved the filing for '{filing.obligation_title}'.",
    )
    db.commit()
    db.refresh(filing)
    return filing


def reject_filing(db: Session, *, filing: Filing, actor: User) -> Filing:
    if filing.status != FilingStatus.DRAFT:
        raise FilingStateError(f"Filing is '{filing.status.value}', not 'draft' -- cannot reject.")

    filing.status = FilingStatus.REJECTED
    filing.human_approved_by = actor.id

    log_audit_event(
        db,
        actor_id=actor.id,
        action="filing.rejected",
        entity_type="filing",
        entity_id=filing.id,
        detail=f"{actor.email} rejected the filing for '{filing.obligation_title}'.",
    )
    db.commit()
    db.refresh(filing)
    return filing


def submit_filing(db: Session, *, filing: Filing, actor: User) -> Filing:
    if filing.status != FilingStatus.APPROVED:
        raise FilingStateError(f"Filing is '{filing.status.value}', not 'approved' -- cannot submit.")

    filing.status = FilingStatus.SUBMITTED
    filing.submitted_at = datetime.now(timezone.utc)

    log_audit_event(
        db,
        actor_id=actor.id,
        action="filing.submitted",
        entity_type="filing",
        entity_id=filing.id,
        detail=(
            f"{actor.email} submitted the filing for '{filing.obligation_title}' "
            "(simulated -- no real government portal submission occurred)."
        ),
    )
    db.commit()
    db.refresh(filing)
    return filing
