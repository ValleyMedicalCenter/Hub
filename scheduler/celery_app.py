# scheduler/celery_app.py
"""
Celery application factory.

Creates and configures a Celery app for the scheduler, using Redis as both
the broker and backend. Integrates with Flask app context if provided and
supports RedBeat persistent scheduler.
"""
from typing import Any, Type

from celery import Celery, Task
from flask import Flask


def make_celery(flask_app: Flask) -> Celery:
    """
    Create a Celery app using Redis for broker and backend.

    Uses redbeat for persistent beat schedule in Redis.
    """
    if not flask_app:
        raise ValueError("Flask app instance must be provided to load config.")

    broker_url = flask_app.config.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    backend_url = flask_app.config.get("CELERY_RESULT_BACKEND", broker_url)

    celery = Celery(
        flask_app.import_name,
        broker=broker_url,
        backend=backend_url,
        include=["scheduler.tasks"],
    )

    celery.conf.update(
        timezone=flask_app.config.get("CELERY_TIMEZONE", "UTC"),
        enable_utc=flask_app.config.get("CELERY_ENABLE_UTC", True),
        beat_scheduler=flask_app.config.get("CELERY_BEAT_SCHEDULER", "redbeat.RedBeatScheduler"),
        redbeat_redis_url=flask_app.config.get("REDBEAT_REDIS_URL", broker_url),
        redbeat_lock_timeout=flask_app.config.get("REDBEAT_LOCK_TIMEOUT", 10),
        task_ignore_result=flask_app.config.get("CELERY_TASK_IGNORE_RESULT", True),
        task_soft_time_limit=flask_app.config.get("CELERY_TASK_SOFT_TIME_LIMIT", 300),
        task_time_limit=flask_app.config.get("CELERY_TASK_TIME_LIMIT", 360),
        beat_schedule=flask_app.config.get("CELERY_BEAT_SCHEDULE", {}),
    )

    taskbase: Type[Task] = celery.Task

    class ContextTask(taskbase):  # type: ignore[misc]
        """Celery Task base class that wraps Flask app context."""

        def __call__(self, *args: Any, **kwargs: Any) -> Any:  # type: ignore[override]
            with flask_app.app_context():
                return taskbase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask  # type: ignore[assignment]

    return celery
