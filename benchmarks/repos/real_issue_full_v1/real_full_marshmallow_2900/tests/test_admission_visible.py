from marshmallow import Schema, fields


def test_required_constant_supplies_its_value_on_load():
    class Event(Schema):
        kind = fields.Constant("created", required=True)

    assert Event().load({})["kind"] == "created"
