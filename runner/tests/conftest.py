"""Setyp pytest."""
import os

import pytest

from runner import create_app as runner_create_app
from runner.model import Project, Task
from web.seed import get_or_create

os.environ["FLASK_ENV"] = "test"
os.environ["FLASK_APP"] = "runner"
os.environ["FLASK_DEBUG"] = "False"

from datetime import datetime
from typing import Any, Generator, Tuple

from dateutil.tz import tzlocal


# default scope is function.
@pytest.fixture()
def client_fixture() -> Generator:
    """Runner client."""
    app = runner_create_app()
    with app.test_client() as client, app.app_context():
        assert app.config["ENV"] == "test"  # noqa: S101

        from runner.extensions import db, runner
        from web.seed import seed

        db.drop_all()
        db.session.commit()

        db.create_all()
        db.session.commit()

        seed(db.session)

        runner.remove_all_jobs()

        assert runner.running  # noqa: S101

        yield client

        if runner.running:
            runner.shutdown(False)


@pytest.fixture(scope="module")
def event_fixture() -> Generator:
    """Create module scoped fixture to share fixture for tests."""
    app = runner_create_app()
    with app.test_client() as client, app.app_context():

        assert app.config["ENV"] == "test"  # noqa: S101

        from runner.extensions import db
        from web.seed import seed

        db.drop_all()
        db.session.commit()

        db.create_all()
        db.session.commit()

        seed(db.session)

        yield client


# pylint: disable=W0613
def demo_task(*kwards: Any, **args: Any) -> int:
    """Demo function with no errors."""
    return 1 + 1


# pylint: disable=W0613
def bad_demo_task(*kwards: Any, **args: Any) -> int:
    """Demo function that will result in error."""
    # pylint: disable=W0104,E0602
    asdf  # type: ignore[name-defined]  # noqa: F821
    return 1 + 1


def create_demo_task(year: int = 2025, sequence: int = 0) -> Tuple[int, int]:
    """Create demo project and task."""
    from runner.extensions import db

    # create a project
    project = get_or_create(
        db.session,
        Project,
        name="Project 1 " + str(datetime.now()),
        cron=1,
        cron_min="1",
        cron_start_date=datetime(year, 1, 1, tzinfo=tzlocal()),
        sequence_tasks=sequence,
        intv=1,
        intv_type="w",
        intv_start_date=datetime(9999, 1, 1, tzinfo=tzlocal()),
        ooff=1,
        ooff_date=datetime(9999, 1, 1, tzinfo=tzlocal()),
    )
    # create a task
    task = get_or_create(
        db.session,
        Task,
        name="Task 1 " + str(project.id),
        source_type_id=6,
        source_code="""select getdate()""",
        project_id=project.id,
        source_query_type_id=4,
        enabled=0,
    )
    return project.id, task.id
