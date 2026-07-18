"""Scheduled task stubs. Real implementations land in Phase 5 (analytics)
and Phase 6 (news + alerts)."""
import logging

from worker.celery_app import celery_app

log = logging.getLogger(__name__)


@celery_app.task
def run_pricing_analytics() -> str:
    log.info("run_pricing_analytics: stub — implemented in Phase 5")
    return "stub"


@celery_app.task
def refresh_news() -> str:
    log.info("refresh_news: stub — implemented in Phase 6")
    return "stub"


@celery_app.task
def scan_alerts() -> str:
    log.info("scan_alerts: stub — implemented in Phase 6")
    return "stub"
