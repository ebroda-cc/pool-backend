from marshmallow import Schema, fields, validate


class AddressCreateSchema(Schema):
    user_id = fields.String(required=True)
    street = fields.String(required=True, validate=validate.Length(min=1))
    number = fields.String(required=True, validate=validate.Length(min=1))
    zip = fields.String(required=True, validate=validate.Length(min=1))
    city = fields.String(required=True, validate=validate.Length(min=1))
    country = fields.String(required=True, validate=validate.Length(min=1))
    country_code = fields.String(required=True, validate=validate.Length(min=1))
    additional = fields.String(load_default=None, allow_none=True)


class AddressUpdateSchema(Schema):
    street = fields.String(validate=validate.Length(min=1))
    number = fields.String(validate=validate.Length(min=1))
    zip = fields.String(validate=validate.Length(min=1))
    city = fields.String(validate=validate.Length(min=1))
    country = fields.String(validate=validate.Length(min=1))
    country_code = fields.String(validate=validate.Length(min=1))
    additional = fields.String(allow_none=True)
