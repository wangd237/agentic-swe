from typing_extensions import TypeAliasType, TypeVar

from pydantic import TypeAdapter


def test_omitted_trailing_alias_type_uses_its_default():
    first = TypeVar("First")
    second = TypeVar("Second", default=int)
    alias = TypeAliasType(
        "Pair", tuple[first, second], type_params=(first, second)
    )
    adapter = TypeAdapter(alias[str])
    assert adapter.validate_python(("name", "42")) == ("name", 42)
