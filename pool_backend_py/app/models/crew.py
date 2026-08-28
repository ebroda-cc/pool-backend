from app.extensions import db
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class CrewCity(db.Model):
    __tablename__ = "crew_cities"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    crew_id = db.Column(db.String(36), db.ForeignKey("crews.id"), nullable=False)
    city = db.Column(db.String(255))
    country = db.Column(db.String(255))
    country_code = db.Column(db.String(8))
    place_id = db.Column(db.String(255))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    crew = db.relationship("Crew", back_populates="cities")

    def to_dict(self):
        return {
            "id": self.id,
            "city": self.city,
            "country": self.country,
            "country_code": self.country_code,
            "place_id": self.place_id,
            "position": {"lat": self.latitude, "lng": self.longitude},
        }


class Crew(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "crews"

    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    abbreviation = db.Column(db.String(32))
    mattermost_username = db.Column(db.String(255))
    additional = db.Column(db.Text)
    status = db.Column(db.String(32), default="active", nullable=False)
    asp_selection = db.Column(db.String(64))

    organisation_id = db.Column(db.String(36), db.ForeignKey("organisations.id"), nullable=True)

    organisation = db.relationship("Organisation", back_populates="crews", foreign_keys=[organisation_id])
    cities = db.relationship("CrewCity", back_populates="crew", cascade="all, delete-orphan", lazy="selectin")
    users = db.relationship("User", back_populates="crew", foreign_keys="User.crew_id")
    roles = db.relationship("Role", back_populates="crew")

    def to_dict(self, include_organisation=True):
        data = {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "abbreviation": self.abbreviation,
            "mattermost_username": self.mattermost_username,
            "additional": self.additional,
            "status": self.status,
            "asp_selection": self.asp_selection,
            "organisation_id": self.organisation_id,
            "cities": [city.to_dict() for city in self.cities],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_organisation and self.organisation:
            data["organisation"] = self.organisation.to_dict()
        return data

    def to_public_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "mattermost_username": self.mattermost_username,
            "organisation_id": self.organisation_id,
            "cities": [city.to_dict() for city in self.cities],
        }
