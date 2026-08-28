import os

from flask import Flask

from app.blueprints import register_blueprints
from app.config import CONFIG_BY_NAME
from app.errors import register_error_handlers
from app.extensions import db, migrate


def create_app(config_name=None):
    app = Flask(__name__)

    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(CONFIG_BY_NAME.get(config_name, CONFIG_BY_NAME["development"]))

    db.init_app(app)
    migrate.init_app(app, db)

    register_error_handlers(app)
    register_blueprints(app)

    # Import models so they are registered on the metadata before
    # `db.create_all()` / Flask-Migrate autogeneration run.
    from app import models  # noqa: F401

    @app.cli.command("init-db")
    def init_db():
        """Create all tables directly, without a migration (quick start / dev only)."""
        db.create_all()
        print("Database tables created.")

    return app
