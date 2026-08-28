from flask import Blueprint, jsonify, request

from app.errors import NotFoundError
from app.extensions import db
from app.models import Address
from app.pagination import paginate
from app.schemas.address import AddressCreateSchema, AddressUpdateSchema

bp = Blueprint("addresses", __name__, url_prefix="/v1/addresses")

create_schema = AddressCreateSchema()
update_schema = AddressUpdateSchema()


def _get_or_404(address_id):
    address = db.session.get(Address, address_id)
    if address is None:
        raise NotFoundError("address", address_id)
    return address


@bp.get("")
def list_addresses():
    query = Address.query
    if user_ids := request.args.getlist("user_id"):
        query = query.filter(Address.user_id.in_(user_ids))
    if city := request.args.get("city"):
        query = query.filter(Address.city.ilike(f"%{city}%"))
    query = query.order_by(Address.created_at.desc())

    items, meta = paginate(query)
    return jsonify({"payload": [a.to_dict() for a in items], "meta": meta})


@bp.get("/<address_id>")
def get_address(address_id):
    return jsonify({"payload": _get_or_404(address_id).to_dict()})


@bp.post("")
def create_address():
    data = create_schema.load(request.get_json(force=True, silent=True) or {})
    address = Address(**data)
    db.session.add(address)
    db.session.commit()
    return jsonify({"payload": address.to_dict()}), 201


@bp.put("/<address_id>")
def update_address(address_id):
    address = _get_or_404(address_id)
    data = update_schema.load(request.get_json(force=True, silent=True) or {}, partial=True)
    for key, value in data.items():
        setattr(address, key, value)
    db.session.commit()
    return jsonify({"payload": address.to_dict()})


@bp.delete("/<address_id>")
def delete_address(address_id):
    address = _get_or_404(address_id)
    db.session.delete(address)
    db.session.commit()
    return jsonify({"payload": address_id})
