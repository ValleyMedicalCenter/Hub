# scheduler/functions.py
"""
Scheduler utility functions for Celery + RedBeat integration.

Provides helpers for adding, deleting, and running scheduled tasks,
as well as computing upcoming fire times for RedBeat entries.
"""

import datetime
from typing import Iterable, List, Tuple

from celery.schedules import crontab, schedule
from redbeat.schedulers import RedBeatScheduler, RedBeatSchedulerEntry

from scheduler.celery_app import celery
from scheduler.extensions import db
from scheduler.model import Task


def _redbeat() -> RedBeatScheduler:
    """Return a RedBeatScheduler instance using the app's Celery."""
    return RedBeatScheduler(app=celery)


def _entry_key(project_id: int, task_id: int, suffix: str) -> str:
    """Generate a unique RedBeat entry name for a task."""
    return f"{project_id}-{task_id}-{suffix}"


def _iter_entries() -> Iterable[Tuple[str, RedBeatSchedulerEntry]]:
    """Iterate over all RedBeat entries in the scheduler."""
    sched = _redbeat().schedule()
    for name, entry in (sched or {}).items():
        yield name, entry


def scheduler_delete_task(task_id: int) -> bool:
    """Delete a RedBeat task entry and clear the task's next_run."""
    status = False
    task = Task.query.filter_by(id=task_id).first()

    for name, entry in list(_iter_entries()):
        try:
            _, entry_task_id, _ = name.split("-", 2)
        except ValueError:
            continue
        if str(entry_task_id) == str(task_id):
            entry.delete()
            status = True

    if task:
        task.next_run = None
        db.session.commit()

    return status


def scheduler_task_runner(task_id: int) -> None:
    """Trigger a task asynchronously via Celery."""
    from scheduler.tasks import run_task

    run_task.delay(int(task_id))


def scheduler_add_task(task_id: int) -> bool:
    """Add a task to the scheduler, respecting cron, interval, or one-off rules."""
    task = Task.query.filter_by(id=task_id).first()
    if not task:
        return False

    task.enabled = 1
    db.session.commit()

    project = task.project

    # Cron scheduling
    if getattr(project, "cron", 0) == 1:
        c = crontab(
            minute=(project.cron_min if project.cron_min is not None else "*"),
            hour=(project.cron_hour if project.cron_hour is not None else "*"),
            day_of_month=(project.cron_day if project.cron_day is not None else "*"),
            month_of_year=(project.cron_month if project.cron_month is not None else "*"),
            day_of_week=(project.cron_week_day if project.cron_week_day is not None else "*"),
        )
        name = _entry_key(project.id, task.id, "cron")
        entry = RedBeatSchedulerEntry(
            name=name,
            task="scheduler.tasks.run_task",
            schedule=c,
            args=(int(task_id),),
            app=celery,
        )
        entry.save()

    # Interval scheduling
    if getattr(project, "intv", 0) == 1:
        v = project.intv_value or 999
        intv_map = {"s": v, "m": v * 60, "h": v * 3600, "d": v * 86400, "w": v * 604800}
        seconds = intv_map.get(project.intv_type or "s", v)
        tz = datetime.datetime.now().astimezone().tzinfo

        name = _entry_key(project.id, task.id, "intv")
        entry = RedBeatSchedulerEntry(
            name=name,
            task="scheduler.tasks.run_task",
            schedule=schedule(run_every=datetime.timedelta(seconds=seconds)),
            args=(int(task_id),),
            app=celery,
            options={"timezone": str(tz) if tz else None},
        )
        entry.save()

    # One-off scheduling
    if getattr(project, "ooff", 0) == 1 and getattr(project, "ooff_date", None):
        from scheduler.tasks import run_task

        run_task.apply_async(args=[int(task_id)], eta=project.ooff_date)

    return True


def _next_fire_times_for_entry(
    entry: RedBeatSchedulerEntry, horizon: datetime.timedelta
) -> List[datetime.datetime]:
    """Compute the next fire times for a RedBeat entry within a given horizon."""
    times: List[datetime.datetime] = []
    now = datetime.datetime.now(datetime.timezone.utc).astimezone()
    end = now + horizon
    sched = entry.schedule
    cursor = now

    for _ in range(200):
        delta = sched.remaining_estimate(cursor)
        if delta.total_seconds() < 0:
            delta = datetime.timedelta(seconds=1)
        nxt = cursor + delta
        if nxt > end:
            break
        times.append(nxt)
        cursor = nxt + datetime.timedelta(seconds=1)

    return times
