import uuid
from datetime import datetime, timezone

from app.extensions import db


def generate_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class UUIDPrimaryKeyMixin:
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
