from marshmallow import validate


def test_oneof_options_ignore_surplus_labels():
    validator = validate.OneOf(choices=["red"], labels=["Red", "unused"])
    assert list(validator.options()) == [("red", "Red")]
    assert list(validate.OneOf(choices=[], labels=["unused"]).options()) == []
