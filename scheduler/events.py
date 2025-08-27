# scheduler/events.py
"""
Celery signal-based logging, replacing APScheduler event listeners.

Writes to scheduler.model.TaskLog to mirror your previous logs.
"""
from __future__ import annotations

from typing import Any, Sequence

from celery import Task as CeleryTask
from celery import signals

from scheduler.extensions import db
from scheduler.model import Task, TaskLog


@signals.task_prerun.connect
def task_prerun_handler(
    sender: CeleryTask,
    task_id: str,
    task: CeleryTask,
    args: Sequence[Any],
    kwargs: dict[str, Any],
    **rest: Any,
) -> None:
    """Approx of APS 'job_submitted' / 'job_added' before run."""
    if not args:
        return

    tid = args[0]
    row: Task | None = Task.query.filter_by(id=tid).first()
    if not row:
        return

    log = TaskLog(task_id=tid, status_id=6, message="Job submitted.")
    db.session.add(log)
    db.session.commit()


@signals.task_success.connect
def task_success_handler(
    sender: CeleryTask,
    result: Any,
    **kwargs: Any,
) -> None:
    """Approx of APS 'job_executed'."""
    args: Sequence[Any] = kwargs.get("args", [])
    if not args:
        return

    tid = args[0]
    row: Task | None = Task.query.filter_by(id=tid).first()
    if not row:
        return

    log = TaskLog(task_id=tid, status_id=6, message="Job executed successfully.")
    db.session.add(log)
    db.session.commit()


@signals.task_failure.connect
def task_failure_handler(
    sender: CeleryTask,
    task_id: str,
    exception: BaseException,
    args: Sequence[Any],
    kwargs: dict[str, Any],
    traceback: Any,
    einfo: Any,
    **rest: Any,
) -> None:
    """Approx of APS 'job_error'."""
    if not args:
        return

    tid = args[0]
    row: Task | None = Task.query.filter_by(id=tid).first()
    if not row:
        return

    log = TaskLog(
        task_id=tid,
        status_id=6,
        error=1,
        message=f"Job error: {exception}\nTrace: {traceback}",
    )
    row.status_id = 2
    db.session.add(log)
    db.session.commit()
