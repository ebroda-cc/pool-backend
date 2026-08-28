from flask import Blueprint, jsonify, request

from app.errors import ApiError, NotFoundError
from app.extensions import db
from app.models import Role, User
from app.schemas.role import RoleBulkCreateSchema, RoleCreateSchema

bp = Blueprint("roles", __name__, url_prefix="/v1/roles")

create_schema = RoleCreateSchema()
bulk_create_schema = RoleBulkCreateSchema()


def _get_or_404(role_id):
    role = db.session.get(Role, role_id)
    if role is None:
        raise NotFoundError("role", role_id)
    return role


@bp.get("")
def list_roles():
    query = Role.query
    if user_ids := request.args.getlist("user_id"):
        query = query.filter(Role.user_id.in_(user_ids))
    if crew_ids := request.args.getlist("crew_id"):
        query = query.filter(Role.crew_id.in_(crew_ids))
    if names := request.args.getlist("name"):
        query = query.filter(Role.name.in_(names))
    roles = query.order_by(Role.created_at.desc()).all()
    return jsonify({"payload": [r.to_dict() for r in roles]})


@bp.post("")
def create_role():
    data = create_schema.load(request.get_json(force=True, silent=True) or {})
    if db.session.get(User, data["user_id"]) is None:
        raise NotFoundError("user", data["user_id"])
    if Role.query.filter_by(user_id=data["user_id"], name=data["name"]).first() is not None:
        raise ApiError(f"user already has role '{data['name']}'", status_code=409)

    role = Role(**data)
    db.session.add(role)
    db.session.commit()
    return jsonify({"payload": role.to_dict()}), 201


@bp.post("/bulk")
def create_roles_bulk():
    data = bulk_create_schema.load(request.get_json(force=True, silent=True) or {})
    created, skipped = [], []
    for user_id in data["user_ids"]:
        if db.session.get(User, user_id) is None:
            raise NotFoundError("user", user_id)
        existing = Role.query.filter_by(user_id=user_id, name=data["name"]).first()
        if existing is not None:
            skipped.append(existing.to_dict())
            continue
        role = Role(user_id=user_id, name=data["name"], crew_id=data.get("crew_id"))
        db.session.add(role)
        created.append(role)
    db.session.commit()
    return (
        jsonify({"payload": {"created": [r.to_dict() for r in created], "skipped": skipped}}),
        201,
    )


@bp.delete("/<role_id>")
def delete_role(role_id):
    role = _get_or_404(role_id)
    db.session.delete(role)
    db.session.commit()
    return jsonify({"payload": role_id})
