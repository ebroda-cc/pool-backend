from marshmallow import Schema, fields, validate

from app.models.role import ROLE_NAMES


class RoleCreateSchema(Schema):
    user_id = fields.String(required=True)
    name = fields.String(required=True, validate=validate.OneOf(ROLE_NAMES))
    crew_id = fields.String(load_default=None, allow_none=True)


class RoleBulkCreateSchema(Schema):
    crew_id = fields.String(load_default=None, allow_none=True)
    user_ids = fields.List(fields.String(), required=True, validate=validate.Length(min=1))
    name = fields.String(required=True, validate=validate.OneOf(ROLE_NAMES))
