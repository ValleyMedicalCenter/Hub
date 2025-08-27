# scheduler/tasks.py
"""
Task runner for Celery.

Calls runner API and mirrors previous scheduler_task_runner semantics.
"""

import requests
from celery import current_app, shared_task
from celery.app.task import Task as CeleryTask

from scheduler.extensions import db
from scheduler.model import Task


@shared_task(bind=True, max_retries=3, name="scheduler.tasks.run_task")
def run_task(self: CeleryTask, task_id: int) -> str:
    """Run a task by calling the runner API asynchronously."""
    task = Task.query.filter_by(id=task_id).first()
    if not task:
        return f"Task {task_id} not found"

    task.status_id = 2
    db.session.commit()

    runner_host = current_app.conf.get("RUNNER_HOST")
    if not runner_host:
        raise RuntimeError("RUNNER_HOST is not configured in app config")

    try:
        requests.get(f"{runner_host}/{task_id}", timeout=60)
        return f"Task {task_id} triggered"
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
