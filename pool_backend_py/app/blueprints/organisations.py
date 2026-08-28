from flask import Blueprint, jsonify, request

from app.errors import NotFoundError
from app.extensions import db
from app.models import Organisation
from app.pagination import paginate
from app.schemas.organisation import OrganisationCreateSchema, OrganisationUpdateSchema

bp = Blueprint("organisations", __name__, url_prefix="/v1/organisations")

create_schema = OrganisationCreateSchema()
update_schema = OrganisationUpdateSchema()


def _get_or_404(organisation_id):
    organisation = db.session.get(Organisation, organisation_id)
    if organisation is None:
        raise NotFoundError("organisation", organisation_id)
    return organisation


@bp.get("")
def list_organisations():
    query = Organisation.query
    if name := request.args.get("name"):
        query = query.filter(Organisation.name.ilike(f"%{name}%"))
    if abbreviation := request.args.get("abbreviation"):
        query = query.filter(Organisation.abbreviation.ilike(f"%{abbreviation}%"))
    if email := request.args.get("email"):
        query = query.filter(Organisation.email.ilike(f"%{email}%"))
    query = query.order_by(Organisation.name.asc())

    items, meta = paginate(query)
    return jsonify({"payload": [o.to_dict() for o in items], "meta": meta})


@bp.get("/<organisation_id>")
def get_organisation(organisation_id):
    return jsonify({"payload": _get_or_404(organisation_id).to_dict()})


@bp.post("")
def create_organisation():
    data = create_schema.load(request.get_json(force=True, silent=True) or {})
    organisation = Organisation(**data)
    db.session.add(organisation)
    db.session.commit()
    return jsonify({"payload": organisation.to_dict()}), 201


@bp.put("/<organisation_id>")
def update_organisation(organisation_id):
    organisation = _get_or_404(organisation_id)
    data = update_schema.load(request.get_json(force=True, silent=True) or {}, partial=True)
    for key, value in data.items():
        setattr(organisation, key, value)
    db.session.commit()
    return jsonify({"payload": organisation.to_dict()})


@bp.delete("/<organisation_id>")
def delete_organisation(organisation_id):
    organisation = _get_or_404(organisation_id)
    db.session.delete(organisation)
    db.session.commit()
    return jsonify({"payload": organisation_id})
