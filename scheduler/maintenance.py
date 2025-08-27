# scheduler/maintenance.py
"""
Scheduler maintenance tasks (Celery + Beat).

Replaces APScheduler periodic tasks.
"""

import logging
import shutil
import time
from pathlib import Path
from typing import Any

import psutil
from celery import Celery
from celery import Task as CeleryTask
from celery import shared_task
from celery.schedules import crontab, schedule
from sqlalchemy import and_, or_, update

from scheduler.celery_app import celery
from scheduler.extensions import db
from scheduler.functions import scheduler_delete_task
from scheduler.model import Task


@celery.on_after_finalize.connect
def setup_periodic_tasks(sender: Celery, **kwargs: Any) -> None:
    """Register periodic tasks with Celery Beat."""
    # job_sync every hour
    sender.add_periodic_task(crontab(minute=19), job_sync.s(), name="job_sync_hourly")

    # temp_clean every 30 seconds
    sender.add_periodic_task(schedule(run_every=30.0), temp_clean.s(), name="temp_clean_30s")


@shared_task(name="scheduler.maintenance.job_sync")
def job_sync() -> None:
    """Sync run times between DB and scheduler (hourly)."""
    try:
        # Reset disabled jobs next_run/est_duration
        db.session.execute(
            update(Task)
            .where(
                and_(
                    Task.enabled == 0,
                    or_(Task.next_run.isnot(None), Task.est_duration.isnot(None)),
                )
            )
            .values(next_run=None, est_duration=None)
        )
        db.session.commit()

        # Remove RedBeat entries for disabled tasks
        for task in Task.query.filter_by(enabled=0).all():
            scheduler_delete_task(task.id)

    except Exception as exc:
        logging.error(str(exc))


def drop_them(temp_path: Path, age: int) -> None:
    """Remove files older than 'age' seconds."""
    for temp_file in temp_path.glob("*/*/*"):
        if temp_file.stat().st_mtime < time.time() - age:
            try:
                if temp_file.is_dir():
                    shutil.rmtree(temp_file)
                elif temp_file.is_file():
                    temp_file.unlink()
            except Exception as exc:
                logging.error(str(exc))


@shared_task(name="scheduler.maintenance.temp_clean")
def temp_clean() -> None:
    """Clean dangling temp files every 30s."""
    try:
        temp_path = Path(__file__).parents[1] / "runner" / "temp"
        if not temp_path.exists():
            return

        # Remove files older than 2 hours
        drop_them(temp_path, 7200)

        # Emergency cleanup if disk space low
        from flask import current_app as app

        disk = psutil.disk_usage("/")
        if disk.free < app.config.get("MIN_DISK_SPACE", 0):
            drop_them(temp_path, 1800)

    except Exception as exc:
        logging.error(str(exc))
