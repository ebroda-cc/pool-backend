from flask import jsonify
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.exceptions import HTTPException

from app.extensions import db


class ApiError(Exception):
    """Base error for expected, user-facing API failures."""

    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        return {"error": self.message, **(self.payload or {})}


class NotFoundError(ApiError):
    status_code = 404

    def __init__(self, resource, resource_id):
        super().__init__(f"{resource} with id '{resource_id}' not found")


class PermissionDeniedError(ApiError):
    status_code = 403

    def __init__(self, message="permission denied"):
        super().__init__(message)


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(err):
        return jsonify(err.to_dict()), err.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(err):
        return jsonify({"error": "validation error", "details": err.messages}), 400

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(err):
        db.session.rollback()
        app.logger.warning("Database integrity error: %s", err)
        return jsonify({"error": "conflicting or invalid reference"}), 409

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        return jsonify({"error": err.description}), err.code

    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(err):
        db.session.rollback()
        app.logger.exception("Unhandled database error")
        return jsonify({"error": "internal server error"}), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        db.session.rollback()
        app.logger.exception("Unhandled exception")
        return jsonify({"error": "internal server error"}), 500
