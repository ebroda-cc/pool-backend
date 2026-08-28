from app.extensions import db
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class User(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255))
    country = db.Column(db.String(255))
    privacy_policy = db.Column(db.Boolean, default=False, nullable=False)
    confirmed = db.Column(db.Boolean, default=False, nullable=False)
    drops_id = db.Column(db.String(64))
    last_login_date = db.Column(db.BigInteger)

    organisation_id = db.Column(db.String(36), db.ForeignKey("organisations.id"), nullable=True)
    crew_id = db.Column(db.String(36), db.ForeignKey("crews.id"), nullable=True)

    organisation = db.relationship("Organisation", back_populates="users", foreign_keys=[organisation_id])
    crew = db.relationship("Crew", back_populates="users", foreign_keys=[crew_id])
    address = db.relationship(
        "Address", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    roles = db.relationship("Role", back_populates="user", cascade="all, delete-orphan", lazy="selectin")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def to_dict(self, include_relations=True):
        data = {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "display_name": self.display_name,
            "country": self.country,
            "privacy_policy": self.privacy_policy,
            "confirmed": self.confirmed,
            "drops_id": self.drops_id,
            "last_login_date": self.last_login_date,
            "organisation_id": self.organisation_id,
            "crew_id": self.crew_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_relations:
            data["address"] = self.address.to_dict() if self.address else None
            data["roles"] = [role.to_dict() for role in self.roles]
        return data

    def to_minimal_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "display_name": self.display_name,
        }
