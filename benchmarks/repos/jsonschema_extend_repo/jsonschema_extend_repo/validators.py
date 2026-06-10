"""从 jsonschema#1125 提炼出的最小 validator extend 实现。"""

from __future__ import annotations

from collections.abc import Iterable


def _default_applicable_validators(schema: dict[str, object]) -> Iterable[tuple[str, object]]:
    """默认返回 schema 中出现的全部关键字。"""
    return schema.items()


def _legacy_ref_applicable_validators(schema: dict[str, object]) -> Iterable[tuple[str, object]]:
    """模拟 legacy validator 在 `$ref` 场景下只应用 `$ref` 本身。"""
    if "$ref" in schema:
        return [("$ref", schema["$ref"])]
    return schema.items()


def create(
    validators: dict[str, object],
    applicable_validators=_default_applicable_validators,
) -> type[object]:
    """创建一个仅保留本 benchmark 所需行为的 validator 类。"""
    selected_applicable_validators = applicable_validators

    class CreatedValidator:
        VALIDATORS = dict(validators)
        applicable_validators = staticmethod(selected_applicable_validators)

        @classmethod
        def applicable_keyword_names(cls, schema: dict[str, object]) -> list[str]:
            return [
                keyword
                for keyword, _ in cls.applicable_validators(schema)
                if keyword in cls.VALIDATORS
            ]

    return CreatedValidator


Draft4Validator = create(
    validators={
        "$ref": object(),
        "maximum": object(),
        "type": object(),
    },
    applicable_validators=_legacy_ref_applicable_validators,
)


def extend(
    validator: type[object],
    validators: dict[str, object] | None = None,
) -> type[object]:
    """基于已有 validator 生成扩展类。"""
    combined = dict(validator.VALIDATORS)
    combined.update(validators or {})

    # 这里故意保留真实 issue 中的缺陷：extend 没有把 applicable_validators 透传给 create。
    return create(validators=combined)
