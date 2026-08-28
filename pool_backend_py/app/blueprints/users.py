from flask import Blueprint, jsonify, request

from app.errors import NotFoundError
from app.extensions import db
from app.models import User
from app.pagination import paginate
from app.schemas.user import UserCreateSchema, UserUpdateSchema

bp = Blueprint("users", __name__, url_prefix="/v1/users")

create_schema = UserCreateSchema()
update_schema = UserUpdateSchema()


def _get_or_404(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError("user", user_id)
    return user


@bp.get("")
def list_users():
    query = User.query
    if email := request.args.get("email"):
        query = query.filter(User.email.ilike(f"%{email}%"))
    if first_name := request.args.get("first_name"):
        query = query.filter(User.first_name.ilike(f"%{first_name}%"))
    if last_name := request.args.get("last_name"):
        query = query.filter(User.last_name.ilike(f"%{last_name}%"))
    if crew_ids := request.args.getlist("crew_id"):
        query = query.filter(User.crew_id.in_(crew_ids))
    if organisation_ids := request.args.getlist("organisation_id"):
        query = query.filter(User.organisation_id.in_(organisation_ids))
    if confirmed := request.args.get("confirmed"):
        query = query.filter(User.confirmed == (confirmed.lower() == "true"))
    query = query.order_by(User.last_name.asc(), User.first_name.asc())

    items, meta = paginate(query)
    return jsonify({"payload": [u.to_dict(include_relations=False) for u in items], "meta": meta})


@bp.get("/<user_id>")
def get_user(user_id):
    return jsonify({"payload": _get_or_404(user_id).to_dict()})


@bp.post("")
def create_user():
    data = create_schema.load(request.get_json(force=True, silent=True) or {})
    user = User(**data)
    db.session.add(user)
    db.session.commit()
    return jsonify({"payload": user.to_dict()}), 201


@bp.put("/<user_id>")
def update_user(user_id):
    user = _get_or_404(user_id)
    data = update_schema.load(request.get_json(force=True, silent=True) or {}, partial=True)
    for key, value in data.items():
        setattr(user, key, value)
    db.session.commit()
    return jsonify({"payload": user.to_dict()})


@bp.delete("/<user_id>")
def delete_user(user_id):
    user = _get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"payload": user_id})
