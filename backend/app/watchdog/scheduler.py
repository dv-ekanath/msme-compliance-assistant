from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.watchdog.scanner import scan_regulations

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def run_scan_job() -> None:
    """Owns its own DB session -- runs on a background thread, independent
    of any request, so it can't use the request-scoped get_db dependency.
    """
    db = SessionLocal()
    try:
        result = scan_regulations(db)
        logger.info(
            "Watchdog scan complete: %d checked, %d changed, %d alerts created",
            result.regulations_checked,
            result.changes_detected,
            result.alerts_created,
        )
    except Exception:
        logger.exception("Watchdog scan failed")
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    settings = get_settings()
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_scan_job,
        "interval",
        hours=settings.watchdog_scan_interval_hours,
        id="watchdog_scan",
    )
    scheduler.start()
    _scheduler = scheduler
    return scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
