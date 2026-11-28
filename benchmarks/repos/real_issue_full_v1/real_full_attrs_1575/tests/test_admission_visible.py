import attr


def test_unimported_classvar_does_not_become_instance_field():
    @attr.s(auto_attribs=True)
    class Example:
        shared: ClassVar[str]
        value: int = 7

    obj = Example()
    assert obj.value == 7
    assert "shared" not in attr.fields_dict(Example)
