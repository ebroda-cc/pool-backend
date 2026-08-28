from flask import request


def paginate(query):
    """Applies ?page=&per_page= to a SQLAlchemy query and returns (items, meta)."""
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except ValueError:
        page = 1
    try:
        per_page = min(max(int(request.args.get("per_page", 20)), 1), 100)
    except ValueError:
        per_page = 20

    total = query.order_by(None).count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    meta = {"page": page, "per_page": per_page, "total": total}
    return items, meta
