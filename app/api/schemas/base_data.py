from marshmallow import Schema, fields

class SpecialtyTypeSchema(Schema):
    id = fields.Integer(dump_only=True)
    sptfather = fields.Integer()
    sptname = fields.String()
    sort = fields.Integer()
    children = fields.List(fields.Nested(lambda: SpecialtyTypeSchema()), dump_only=True)