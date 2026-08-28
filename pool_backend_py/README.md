# Pool Backend (Flask / MySQL)

Python/Flask + Flask-SQLAlchemy port of the core data layer of the Go
backend in the repository root, backed by MySQL instead of MongoDB.

## Scope of this port

This is a **starter skeleton**, not a full 1:1 port of the Go application.
It covers five core domains as a template for the remaining ~25 modules:

- `Organisation`
- `Crew` (with embedded cities as a `crew_cities` table)
- `Address`
- `User`
- `Role` (the former `pool_roles` collection — role assignments per user)

**Deliberately left out of this first pass** (see the modules that were
skipped in the Go app: `Event`, `Deposit`, `Taking`, `Mailbox`, `Message`,
`Newsletter`, `Avatar`, `NVM`, `Active`, `Participation`, etc.):

- **Authentication/authorization.** The Go app authenticates against an
  OAuth2/Hydra server and enforces per-role permissions on every endpoint
  (`AccessToken`, `token.Roles.Validate(...)`, etc.). None of that is
  implemented here — every endpoint is open. Before deploying this
  anywhere reachable, add an auth layer (e.g. `Flask-JWT-Extended` or
  `authlib` against the existing Hydra server) and re-introduce permission
  checks per endpoint, mirroring the `*Permission` functions in
  `models/*.go` of the Go app.
- **NATS event bus** (`vcago.Nats.Publish(...)` in the Go handlers).
- **File storage** (GridFS-backed avatars/receipts).
- **IDjango sync calls** (the `dao.IDjango.Post(...)` webhooks).

## Relational schema notes

MongoDB documents were flattened into normalized tables:

- `User.roles` (pool roles) → `roles` table, one row per
  `(user_id, name)`, unique constraint.
- `User.address` (embedded) → `addresses` table with `user_id` FK
  (one-to-one).
- `Crew.cities` (embedded array) → `crew_cities` table with `crew_id` FK.
- `Organisation.default_asp_id` and `User.organisation_id` form a circular
  reference; the `organisations.default_asp_id` FK is created with
  `use_alter=True` so Alembic/MySQL can apply it as a deferred
  `ALTER TABLE`.
- The Go `UserCrew` join document was collapsed into a plain
  `users.crew_id` foreign key — crew membership doesn't carry any of its
  own fields in this simplified schema.

## Getting started

```bash
cd pool_backend_py
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env   # adjust DB_* to your local MySQL

# create the schema (either one):
flask --app run.py db upgrade      # once migrations/ has been initialized
# or, for a quick start without migrations:
flask --app run.py init-db

flask --app run.py run
```

Or via Docker Compose (spins up MySQL too):

```bash
docker compose up --build
```

### Setting up migrations

`Flask-Migrate` (Alembic) is wired up but `migrations/` isn't generated
yet, since that requires a live database connection:

```bash
flask --app run.py db init
flask --app run.py db migrate -m "initial schema"
flask --app run.py db upgrade
```

## Running the tests

The test suite runs against an in-memory SQLite database, so it needs no
MySQL instance:

```bash
pip install -r requirements-dev.txt
pytest
```

## API overview

All routes are prefixed with `/v1`, matching the Go API's base path.

| Resource      | Routes                                                                 |
|---------------|-------------------------------------------------------------------------|
| Organisations | `GET/POST /v1/organisations`, `GET/PUT/DELETE /v1/organisations/<id>`  |
| Crews         | `GET/POST /v1/crews`, `GET/PUT/DELETE /v1/crews/<id>`, `GET /v1/crews/public` |
| Addresses     | `GET/POST /v1/addresses`, `GET/PUT/DELETE /v1/addresses/<id>`          |
| Users         | `GET/POST /v1/users`, `GET/PUT/DELETE /v1/users/<id>`                  |
| Roles         | `GET/POST /v1/roles`, `POST /v1/roles/bulk`, `DELETE /v1/roles/<id>`   |

List endpoints support `?page=&per_page=` plus per-resource filters (see
each blueprint in `app/blueprints/`). Responses are shaped as
`{"payload": ..., "meta": {...}}` on lists and `{"payload": ...}` on single
resources, mirroring the Go API's response envelope.

## Extending to the remaining modules

To port another Go module (e.g. `Event`):

1. Add a `db.Model` in `app/models/` (flatten embedded Mongo sub-documents
   into their own tables/FKs as needed).
2. Add `marshmallow` create/update schemas in `app/schemas/`.
3. Add a blueprint in `app/blueprints/` with the same CRUD pattern used
   here, and register it in `app/blueprints/__init__.py`.
4. Re-generate a migration: `flask --app run.py db migrate -m "add <model>"`.
