from marshmallow import Schema, fields, validate


class OrganisationCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    abbreviation = fields.String(load_default=None, allow_none=True)
    email = fields.Email(load_default=None, allow_none=True)
    default_asp_id = fields.String(load_default=None, allow_none=True)
    options = fields.List(fields.String(), load_default=list)


class OrganisationUpdateSchema(Schema):
    name = fields.String(validate=validate.Length(min=1, max=255))
    abbreviation = fields.String(allow_none=True)
    email = fields.Email(allow_none=True)
    default_asp_id = fields.String(allow_none=True)
    options = fields.List(fields.String())
