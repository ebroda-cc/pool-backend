from app.extensions import db
from app.models.base import UUIDPrimaryKeyMixin, utcnow

ROLE_NAMES = (
    "asp",
    "finance",
    "operation",
    "education",
    "network",
    "socialmedia",
    "awareness",
    "other",
    "supporter",
)


class Role(db.Model, UUIDPrimaryKeyMixin):
    """A pool role assigned to a user (formerly the `pool_roles` Mongo collection)."""

    __tablename__ = "roles"
    __table_args__ = (db.UniqueConstraint("user_id", "name", name="uq_role_user_name"),)

    name = db.Column(db.String(32), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False)
    crew_id = db.Column(db.String(36), db.ForeignKey("crews.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship("User", back_populates="roles")
    crew = db.relationship("Crew", back_populates="roles")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "user_id": self.user_id,
            "crew_id": self.crew_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
