from marshmallow import Schema, fields

class UserSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    phone = fields.String(required=True)
    extra_info = fields.String(missing="")

class DeeperSchema(Schema):
    user_id = fields.String(required=True)
    name = fields.String(required=True)
    phone = fields.String(required=True)
    extra_info = fields.String(missing="")
    memo = fields.String(missing="")