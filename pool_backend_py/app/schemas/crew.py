from marshmallow import Schema, fields, validate


class PositionSchema(Schema):
    lat = fields.Float(load_default=None, allow_none=True)
    lng = fields.Float(load_default=None, allow_none=True)


class CitySchema(Schema):
    city = fields.String(load_default=None, allow_none=True)
    country = fields.String(load_default=None, allow_none=True)
    country_code = fields.String(load_default=None, allow_none=True)
    place_id = fields.String(load_default=None, allow_none=True)
    position = fields.Nested(PositionSchema, load_default=dict)


class CrewCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=255))
    email = fields.Email(load_default=None, allow_none=True)
    abbreviation = fields.String(load_default=None, allow_none=True)
    mattermost_username = fields.String(load_default=None, allow_none=True)
    additional = fields.String(load_default=None, allow_none=True)
    organisation_id = fields.String(load_default=None, allow_none=True)
    status = fields.String(load_default="active")
    asp_selection = fields.String(load_default=None, allow_none=True)
    cities = fields.List(fields.Nested(CitySchema), load_default=list)


class CrewUpdateSchema(Schema):
    name = fields.String(validate=validate.Length(min=1, max=255))
    email = fields.Email(allow_none=True)
    abbreviation = fields.String(allow_none=True)
    mattermost_username = fields.String(allow_none=True)
    additional = fields.String(allow_none=True)
    organisation_id = fields.String(allow_none=True)
    status = fields.String()
    asp_selection = fields.String(allow_none=True)
    cities = fields.List(fields.Nested(CitySchema))
