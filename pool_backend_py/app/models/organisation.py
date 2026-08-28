from app.extensions import db
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Organisation(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "organisations"

    name = db.Column(db.String(255), nullable=False)
    abbreviation = db.Column(db.String(32))
    email = db.Column(db.String(255))
    options = db.Column(db.JSON, default=list, nullable=False)

    # Soft reference to the default ASP user. Kept as a plain FK with
    # use_alter so the circular organisations<->users dependency can be
    # created (MySQL/Alembic apply it as a deferred ALTER TABLE).
    default_asp_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", use_alter=True, name="fk_organisation_default_asp"),
        nullable=True,
    )

    default_asp = db.relationship("User", foreign_keys=[default_asp_id], post_update=True)
    crews = db.relationship("Crew", back_populates="organisation", lazy="selectin")
    users = db.relationship(
        "User",
        back_populates="organisation",
        foreign_keys="User.organisation_id",
        lazy="selectin",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "abbreviation": self.abbreviation,
            "email": self.email,
            "options": self.options or [],
            "default_asp_id": self.default_asp_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
