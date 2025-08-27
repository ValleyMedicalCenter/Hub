# scheduler/web.py
"""
Flask blueprint exposing scheduler API endpoints.

Provides task listing, add, delete, run, pause, resume operations.
"""

import datetime
import logging
import re
from itertools import groupby

from flask import Blueprint, Response, jsonify

from scheduler.functions import (
    _iter_entries,
    _next_fire_times_for_entry,
    scheduler_add_task,
    scheduler_delete_task,
    scheduler_task_runner,
)
from scheduler.model import Task

web_bp = Blueprint("web_bp", __name__)


def _task_id_from_entry(name: str) -> int | None:
    """Extract task_id from RedBeat entry name."""
    try:
        _, tid, _ = name.split("-", 2)
        return int(tid)
    except ValueError:
        return None


@web_bp.route("/api")
def alive() -> Response:
    """Return a simple health check for the API."""
    return jsonify({"status": "alive"})


@web_bp.route("/api/schedule")
def schedule_view() -> Response:
    """Return upcoming scheduled tasks within the next 24 hours."""
    tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
    now = datetime.datetime.now(tz)
    tomorrow = now + datetime.timedelta(hours=24)

    hour_list = ["now"]
    ptr = now
    while ptr < tomorrow:
        ptr += datetime.timedelta(hours=1)
        hour_list.append(ptr.strftime("%H:00"))

    active = []
    horizon = datetime.timedelta(hours=24)

    for name, entry in _iter_entries():
        if not re.match(r"^\d+-\d+-.+?$", name) or not entry.enabled:
            continue
        for when in _next_fire_times_for_entry(entry, horizon):
            msg = (
                "now"
                if when.replace(minute=0, second=0, microsecond=0)
                == now.replace(minute=0, second=0, microsecond=0)
                else when.strftime("%H:00")
            )
            active.append({"message": msg, "date": when})

    active.sort(
        key=lambda a: (
            a["date"] if isinstance(a["date"], datetime.datetime) else datetime.datetime.min
        )
    )
    groups = {k: list(g) for k, g in groupby(active, lambda a: a["message"])}

    return jsonify([{"case": h, "count": len(groups.get(h, []))} for h in hour_list])


@web_bp.route("/api/add/<int:task_id>")
def add_task(task_id: int) -> Response:
    """Add a task to the scheduler by task ID."""
    if not Task.query.filter_by(id=task_id).first():
        return jsonify({"error": "Invalid job."})
    try:
        scheduler_delete_task(task_id)
        if scheduler_add_task(task_id):
            return jsonify({"message": "Scheduler: task job added!"})
        return jsonify({"message": "Scheduler: failed to create job!"})
    except Exception as exc:
        logging.error(str(exc))
        return jsonify({"error": f"Scheduler (add job): {exc}"})


@web_bp.route("/api/delete/<int:task_id>")
def delete_task(task_id: int) -> Response:
    """Delete a scheduler task by task ID."""
    if not Task.query.filter_by(id=task_id).first():
        return jsonify({"error": "Invalid job."})
    if scheduler_delete_task(task_id):
        return jsonify({"message": "Scheduler: task job deleted!"})
    return jsonify({"message": "Scheduler: failed to delete job!"})


@web_bp.route("/api/run/<int:task_id>")
def run_task_endpoint(task_id: int) -> Response:
    """Trigger a task immediately by task ID."""
    try:
        scheduler_task_runner(task_id)
        return jsonify({"message": "Scheduler: task job started!"})
    except Exception as exc:
        return jsonify({"error": f"Scheduler (run task): {exc}"})


@web_bp.route("/api/run/<int:task_id>/delay/<int:minutes>")
def run_task_delay(task_id: int, minutes: int) -> Response:
    """Schedule a task to run after a delay in minutes."""
    from scheduler.tasks import run_task

    run_task.apply_async(args=[task_id], countdown=minutes * 60)
    return jsonify({"message": "Scheduler: task scheduled!"})


@web_bp.route("/api/delete")
def delete_all_tasks() -> Response:
    """Delete all scheduler tasks."""
    count = 0
    for name, entry in list(_iter_entries()):
        if re.match(r"^\d+-\d+-.+?$", name):
            entry.delete()
            count += 1
    return jsonify({"message": f"Scheduler: all jobs deleted! ({count})"})


@web_bp.route("/api/pause")
def pause_all_tasks() -> Response:
    """Pause all scheduler tasks."""
    changed = 0
    for _, entry in _iter_entries():
        if entry.enabled:
            entry.enabled = False
            entry.save()
            changed += 1
    return jsonify({"message": f"Scheduler: all jobs paused! ({changed})"})


@web_bp.route("/api/resume")
def resume_all_tasks() -> Response:
    """Resume all paused scheduler tasks."""
    changed = 0
    for _, entry in _iter_entries():
        if not entry.enabled:
            entry.enabled = True
            entry.save()
            changed += 1
    return jsonify({"message": f"Scheduler: all jobs resumed! ({changed})"})


@web_bp.route("/api/kill")
def kill_all_tasks() -> Response:
    """Disable all enabled beat entries (stop requires manual process stop)."""
    changed = 0
    for _, entry in _iter_entries():
        if entry.enabled:
            entry.enabled = False
            entry.save()
            changed += 1
    return jsonify(
        {
            "message": f"Scheduler: beat entries disabled ({changed}). Stop beat process to fully kill."
        }
    )


@web_bp.route("/api/jobs")
def get_jobs() -> Response:
    """Return all task IDs present in the scheduler."""
    ids = [
        _task_id_from_entry(name)
        for name, _ in _iter_entries()
        if _task_id_from_entry(name) is not None
    ]
    return jsonify(ids)


@web_bp.route("/api/details")
def get_jobs_details() -> Response:
    """Return details of all scheduled tasks including next run time."""
    details = []
    horizon = datetime.timedelta(hours=24)
    for name, entry in _iter_entries():
        tid = _task_id_from_entry(name)
        if tid is None:
            continue
        nxt = None
        try:
            times = _next_fire_times_for_entry(entry, horizon)
            nxt = times[0] if times else None
        except Exception:
            nxt = None
        details.append({"name": name, "job_id": name, "next_run_time": nxt, "id": tid})
    return jsonify(details)


@web_bp.route("/api/scheduled")
def get_scheduled_jobs() -> Response:
    """Return task IDs for currently enabled tasks."""
    ids = [
        _task_id_from_entry(name)
        for name, entry in _iter_entries()
        if entry.enabled and _task_id_from_entry(name) is not None
    ]
    return jsonify(ids)


@web_bp.route("/api/delete-orphans")
def delete_orphans() -> Response:
    """Delete scheduler tasks that no longer exist in the database."""
    removed = 0
    for name, entry in list(_iter_entries()):
        tid = _task_id_from_entry(name)
        if tid is None:
            continue
        if Task.query.filter_by(id=tid).count() == 0:
            entry.delete()
            removed += 1
    return jsonify({"message": f"Scheduler: orphans deleted! ({removed})"})
