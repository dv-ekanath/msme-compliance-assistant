from __future__ import annotations

from datetime import date

from app.domain.enums import ObligationFrequency, ObligationStatus, ObligationType

RiskBand = str  # Literal["low", "medium", "high"], kept as str for SQLAlchemy/Pydantic simplicity

# Mirrors services/compliance.py's DUE_SOON_WINDOW_DAYS. Not imported from
# there to keep this module DB/service-free (see module docstring below) --
# both constants encode the same "due soon" policy and should be changed
# together if that policy ever changes.
_DUE_SOON_WINDOW_DAYS = 14

_TYPE_WEIGHT: dict[ObligationType, float] = {
    ObligationType.PAYMENT: 1.2,
    ObligationType.FILING: 1.15,
    ObligationType.RENEWAL: 1.0,
    ObligationType.REGISTRATION: 0.9,
}

_FREQUENCY_WEIGHT: dict[ObligationFrequency | None, float] = {
    ObligationFrequency.MONTHLY: 1.2,
    ObligationFrequency.QUARTERLY: 1.1,
    ObligationFrequency.ANNUALLY: 1.0,
    ObligationFrequency.ONE_TIME: 0.9,
    None: 0.9,
}


def score_obligation(
    *,
    status: ObligationStatus,
    obligation_type: ObligationType,
    frequency: ObligationFrequency | None,
    due_date: date | None,
    today: date,
) -> float:
    """Deterministic 0-100 heuristic risk score for one APPLICABLE
    obligation. No LLM/ML involved -- see CLAUDE.md rule 4 (deterministic
    core, LLM for explanation only).

    Base score comes from due-date status (how urgent), then scaled by
    obligation_type (cash-penalty exposure: PAYMENT/FILING > RENEWAL/
    REGISTRATION) and frequency (a missed MONTHLY obligation compounds
    faster than an ANNUALLY one).
    """
    if status == ObligationStatus.COMPLETED:
        return 0.0

    if status == ObligationStatus.OVERDUE:
        days_overdue = (today - due_date).days if due_date else 0
        base = 60.0 + min(30.0, days_overdue * 2.0)
    elif status == ObligationStatus.DUE_SOON:
        days_until_due = (due_date - today).days if due_date else 0
        proximity = max(0.0, min(1.0, (_DUE_SOON_WINDOW_DAYS - days_until_due) / _DUE_SOON_WINDOW_DAYS))
        base = 30.0 + proximity * 20.0
    else:  # PENDING (no due date yet, or due date beyond the due-soon window)
        base = 10.0

    score = base * _TYPE_WEIGHT.get(obligation_type, 1.0) * _FREQUENCY_WEIGHT.get(frequency, 1.0)
    return max(0.0, min(100.0, score))


def band_for_score(score: float) -> RiskBand:
    if score < 34:
        return "low"
    if score < 67:
        return "medium"
    return "high"


def explain_risk(
    *,
    status: ObligationStatus,
    obligation_type: ObligationType,
    frequency: ObligationFrequency | None,
    band: RiskBand,
) -> str:
    """Deterministic, templated explanation -- no LLM call. Keeps risk
    explanations testable and demo-reliable; see CLAUDE.md rule 4.
    """
    if status == ObligationStatus.COMPLETED:
        return "Completed for the current period -- no outstanding risk."

    frequency_label = frequency.value if frequency else "one-time"
    type_label = obligation_type.value.replace("_", " ")

    if status == ObligationStatus.OVERDUE:
        return (
            f"Overdue {type_label} obligation ({frequency_label}) -- {band} risk. "
            "Complete it as soon as possible to avoid penalties or interest."
        )
    if status == ObligationStatus.DUE_SOON:
        return (
            f"Deadline approaching for this {type_label} obligation ({frequency_label}) -- {band} risk "
            "based on proximity to the due date."
        )
    return f"No immediate deadline pressure yet -- {band} risk. Monitor as the due date approaches."
