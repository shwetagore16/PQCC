"""
workers/celery_app.py — Celery application factory.

Brokers: Redis (task queue)
Backend: Redis (result store)
Serialisation: JSON (safe, human-readable)
"""

from __future__ import annotations

from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

from app.core.config import get_settings

settings = get_settings()

# ── Application factory ───────────────────────────────────────────────────────

celery_app = Celery(
    "pqss",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks.discovery",
        "app.workers.tasks.tls_scan",
        "app.workers.tasks.cbom",
        "app.workers.tasks.ai_scoring",
    ],
)

# ── Configuration ─────────────────────────────────────────────────────────────

celery_app.conf.update(
    # Serialisation
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task behaviour
    task_acks_late=True,               # ACK only after completion (at-least-once)
    task_reject_on_worker_lost=True,   # Re-queue if worker dies mid-task
    task_track_started=True,
    result_expires=86_400,             # 24h TTL for results

    # Concurrency — adjust per deployment
    worker_concurrency=4,
    worker_prefetch_multiplier=1,      # Fair scheduling for long-running scans

    # Rate limiting defaults (individual tasks can override)
    task_default_rate_limit="60/m",

    # Queue routing
    task_default_queue="default",
    task_queues=(
        Queue("default",   Exchange("default"),   routing_key="default"),
        Queue("discovery", Exchange("discovery"), routing_key="discovery"),
        Queue("scanning",  Exchange("scanning"),  routing_key="scanning"),
        Queue("ai",        Exchange("ai"),        routing_key="ai"),
    ),
    task_routes={
        "app.workers.tasks.discovery.*": {"queue": "discovery"},
        "app.workers.tasks.tls_scan.*":  {"queue": "scanning"},
        "app.workers.tasks.cbom.*":      {"queue": "scanning"},
        "app.workers.tasks.ai_scoring.*": {"queue": "ai"},
    },

    # Periodic tasks (beat schedule)
    beat_schedule={
        "refresh-asset-discovery-daily": {
            "task": "app.workers.tasks.discovery.refresh_all_assets",
            "schedule": crontab(hour=2, minute=0),  # 02:00 UTC daily
            "options": {"queue": "discovery"},
        },
        "rescore-hndl-hourly": {
            "task": "app.workers.tasks.ai_scoring.rescore_hndl",
            "schedule": crontab(minute=0),           # top of every hour
            "options": {"queue": "ai"},
        },
    },
)
