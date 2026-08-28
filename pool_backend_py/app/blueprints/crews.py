from flask import Blueprint, jsonify, request

from app.errors import NotFoundError
from app.extensions import db
from app.models import Crew, CrewCity
from app.pagination import paginate
from app.schemas.crew import CrewCreateSchema, CrewUpdateSchema

bp = Blueprint("crews", __name__, url_prefix="/v1/crews")

create_schema = CrewCreateSchema()
update_schema = CrewUpdateSchema()


def _get_or_404(crew_id):
    crew = db.session.get(Crew, crew_id)
    if crew is None:
        raise NotFoundError("crew", crew_id)
    return crew


def _cities_from_payload(cities_data):
    cities = []
    for city in cities_data or []:
        position = city.get("position") or {}
        cities.append(
            CrewCity(
                city=city.get("city"),
                country=city.get("country"),
                country_code=city.get("country_code"),
                place_id=city.get("place_id"),
                latitude=position.get("lat"),
                longitude=position.get("lng"),
            )
        )
    return cities


@bp.get("")
def list_crews():
    query = Crew.query
    if name := request.args.get("name"):
        query = query.filter(Crew.name.ilike(f"%{name}%"))
    if status := request.args.get("status"):
        query = query.filter(Crew.status == status)
    if email := request.args.get("email"):
        query = query.filter(Crew.email.ilike(f"%{email}%"))
    if organisation_ids := request.args.getlist("organisation_id"):
        query = query.filter(Crew.organisation_id.in_(organisation_ids))
    query = query.order_by(Crew.name.asc())

    items, meta = paginate(query)
    return jsonify({"payload": [c.to_dict() for c in items], "meta": meta})


@bp.get("/public")
def list_crews_public():
    query = Crew.query.filter(Crew.status == "active").order_by(Crew.name.asc())
    items, meta = paginate(query)
    return jsonify({"payload": [c.to_public_dict() for c in items], "meta": meta})


@bp.get("/<crew_id>")
def get_crew(crew_id):
    return jsonify({"payload": _get_or_404(crew_id).to_dict()})


@bp.post("")
def create_crew():
    data = create_schema.load(request.get_json(force=True, silent=True) or {})
    cities = _cities_from_payload(data.pop("cities", []))
    crew = Crew(**data, cities=cities)
    db.session.add(crew)
    db.session.commit()
    return jsonify({"payload": crew.to_dict()}), 201


@bp.put("/<crew_id>")
def update_crew(crew_id):
    crew = _get_or_404(crew_id)
    data = update_schema.load(request.get_json(force=True, silent=True) or {}, partial=True)
    if "cities" in data:
        crew.cities = _cities_from_payload(data.pop("cities"))
    for key, value in data.items():
        setattr(crew, key, value)
    db.session.commit()
    return jsonify({"payload": crew.to_dict()})


@bp.delete("/<crew_id>")
def delete_crew(crew_id):
    crew = _get_or_404(crew_id)
    db.session.delete(crew)
    db.session.commit()
    return jsonify({"payload": crew_id})
