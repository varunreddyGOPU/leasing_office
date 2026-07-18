import os

from celery import Celery
from celery.schedules import crontab

redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("auburn_worker", broker=redis_url, backend=redis_url)
celery_app.conf.timezone = "America/Detroit"
celery_app.conf.broker_connection_retry_on_startup = True
celery_app.autodiscover_tasks(["worker"])

celery_app.conf.beat_schedule = {
    # Phase 5: pricing analytics — nightly 02:00 ET
    "nightly-pricing-analytics": {
        "task": "worker.tasks.run_pricing_analytics",
        "schedule": crontab(hour=2, minute=0),
    },
    # Phase 6: local news fetch — every 3 hours
    "news-refresh": {
        "task": "worker.tasks.refresh_news",
        "schedule": crontab(minute=15, hour="*/3"),
    },
    # Phase 6: renewal-window / alert outbox scan — daily 06:00 ET
    "alerts-scan": {
        "task": "worker.tasks.scan_alerts",
        "schedule": crontab(hour=6, minute=0),
    },
}
