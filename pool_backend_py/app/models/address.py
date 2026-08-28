from app.extensions import db
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Address(db.Model, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "addresses"

    street = db.Column(db.String(255), nullable=False)
    number = db.Column(db.String(32), nullable=False)
    zip = db.Column(db.String(32), nullable=False)
    city = db.Column(db.String(255), nullable=False)
    country = db.Column(db.String(255), nullable=False)
    country_code = db.Column(db.String(8), nullable=False)
    additional = db.Column(db.String(255))

    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=False, unique=True)
    user = db.relationship("User", back_populates="address")

    def to_dict(self):
        return {
            "id": self.id,
            "street": self.street,
            "number": self.number,
            "zip": self.zip,
            "city": self.city,
            "country": self.country,
            "country_code": self.country_code,
            "additional": self.additional,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
