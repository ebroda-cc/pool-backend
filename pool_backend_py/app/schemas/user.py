from marshmallow import Schema, fields, validate


class UserCreateSchema(Schema):
    email = fields.Email(required=True)
    first_name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    last_name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    display_name = fields.String(load_default=None, allow_none=True)
    country = fields.String(load_default=None, allow_none=True)
    privacy_policy = fields.Boolean(load_default=False)
    confirmed = fields.Boolean(load_default=False)
    drops_id = fields.String(load_default=None, allow_none=True)
    organisation_id = fields.String(load_default=None, allow_none=True)
    crew_id = fields.String(load_default=None, allow_none=True)


class UserUpdateSchema(Schema):
    email = fields.Email()
    first_name = fields.String(validate=validate.Length(min=1, max=255))
    last_name = fields.String(validate=validate.Length(min=1, max=255))
    display_name = fields.String(allow_none=True)
    country = fields.String(allow_none=True)
    privacy_policy = fields.Boolean()
    confirmed = fields.Boolean()
    drops_id = fields.String(allow_none=True)
    organisation_id = fields.String(allow_none=True)
    crew_id = fields.String(allow_none=True)
