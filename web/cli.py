"""EM Web Custom CLI."""
import sys
from pathlib import Path

from flask import Blueprint
from flask import current_app as app
from flask.cli import with_appcontext

from web import model
from web.extensions import db

cli_bp = Blueprint("cli", __name__)


@cli_bp.cli.command("create_db")
@with_appcontext
def create_db() -> None:
    """Add command to create the test database."""
    if app.config["ENV"] in ["test", "development"]:

        # pylint: disable=W0611
        from web.model import (  # noqa: F401
            Connection,
            ConnectionDatabase,
            ConnectionDatabaseType,
            ConnectionFtp,
            ConnectionGpg,
            ConnectionSftp,
            ConnectionSmb,
            ConnectionSsh,
            Login,
            LoginType,
            Project,
            QuoteLevel,
            Task,
            TaskDestinationFileType,
            TaskFile,
            TaskLog,
            TaskProcessingType,
            TaskSourceQueryType,
            TaskSourceType,
            TaskStatus,
            User,
        )

        db.drop_all()
        db.session.commit()

        db.create_all()
        db.session.commit()


@cli_bp.cli.command("reset_db")
@with_appcontext
def reset_db() -> None:
    """Add command to clear the database."""
    db.drop_all()

    db.engine.execute("drop table if exists alembic_version")


@cli_bp.cli.command("seed")
@with_appcontext
def db_seed() -> None:
    """Add command to seed the database."""
    sys.path.append(str(Path(__file__).parents[1]) + "/scripts")
    from database import seed

    seed(db.session, model)


@cli_bp.cli.command("seed_demo")
@with_appcontext
def db_seed_demo() -> None:
    """Add command to seed the database for a demo."""
    from .seed import seed_demo

    seed_demo()
