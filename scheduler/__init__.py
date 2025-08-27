# scheduler/__init__.py
"""
Flask application factory for the scheduler.

Sets up Flask, SQLAlchemy, and Celery integration.
Provides unified error handling and blueprint registration.
"""

import logging
import os
from typing import Type

from celery import Celery
from flask import Flask, Response, jsonify, make_response
from werkzeug.exceptions import HTTPException

from scheduler.celery_app import make_celery
from scheduler.extensions import db

# Module-level celery reference (attached to app for safety)
celery: Celery | None = None


def create_app() -> Flask:
    """Create and configure the Flask app."""
    app = Flask(__name__)
    env = os.environ.get("FLASK_ENV", "production")
    app.config["ENV"] = env

    # Load configuration from custom or default

    if env == "development":
        try:
            from config_cust import DevConfig as CustDevConfig

            app.config.from_object(CustDevConfig())
        except ImportError:
            from config import DevConfig

            app.config.from_object(DevConfig())
    elif env == "demo":
        try:
            from config_cust import DemoConfig as CustDemoConfig

            app.config.from_object(CustDemoConfig())
        except ImportError:
            from config import DemoConfig

            app.config.from_object(DemoConfig())
    elif env == "test":
        try:
            from config_cust import TestConfig as CustTestConfig

            app.config.from_object(CustTestConfig())
        except ImportError:
            from config import TestConfig

            app.config.from_object(TestConfig())
    else:
        try:
            from config_cust import Config as CustConfig

            app.config.from_object(CustConfig())
        except ImportError:
            from config import Config

            app.config.from_object(Config())

    # Initialize extensions
    db.init_app(app)

    # Import blueprints and event hooks
    from scheduler import events  # noqa: F401
    from scheduler import web

    app.register_blueprint(web.web_bp)

    logging.basicConfig(level=logging.WARNING)

    # Attach Celery instance to the app
    app.celery = make_celery(app)

    # Unified error handlers
    @app.errorhandler(404)
    def not_found(error: HTTPException) -> Response:
        return make_response(jsonify({"error": str(error)}), 404)

    @app.errorhandler(500)
    def server_error(error: HTTPException) -> Response:
        return make_response(jsonify({"error": str(error)}), 500)

    return app


# Create app and celery instances at module level
app = create_app()
celery = app.celery  # type: ignore[attr-defined]

if __name__ == "__main__":  # pragma: no cover
    app.run(port=5001)
