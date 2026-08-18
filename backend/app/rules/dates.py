from __future__ import annotations

from datetime import date, timedelta

from app.domain.enums import ObligationFrequency


def preceding_month_end(today: date) -> date:
    first_of_this_month = date(today.year, today.month, 1)
    return first_of_this_month - timedelta(days=1)


def preceding_quarter_end(today: date) -> date:
    quarter_start_month = ((today.month - 1) // 3) * 3 + 1  # 1, 4, 7, or 10
    first_of_this_quarter = date(today.year, quarter_start_month, 1)
    return first_of_this_quarter - timedelta(days=1)


def periodic_due_date(
    today: date, frequency: ObligationFrequency, deadline_days_after_period_end: int
) -> date:
    """Due date for the most recently closed filing period.

    Deliberately does NOT roll forward once passed -- a due date that has
    elapsed should read as overdue until the next period's due date
    naturally supersedes it as `today` crosses into the next period.
    """
    if frequency == ObligationFrequency.QUARTERLY:
        period_end = preceding_quarter_end(today)
    elif frequency == ObligationFrequency.MONTHLY:
        period_end = preceding_month_end(today)
    else:
        raise ValueError(f"periodic_due_date does not support frequency={frequency!r}")

    return period_end + timedelta(days=deadline_days_after_period_end)
