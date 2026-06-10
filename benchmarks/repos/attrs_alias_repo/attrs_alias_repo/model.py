"""从 python-attrs/attrs#1479 提炼出的最小 alias 可见性实现。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable


@dataclass(slots=True)
class FieldSpec:
    """字段声明阶段的最小配置对象。"""

    alias: str | None = None


@dataclass(slots=True)
class Attribute:
    """类构建阶段交给 field_transformer 的最小字段对象。"""

    name: str
    alias: str | None = None


FieldTransformer = Callable[[type[object], list[Attribute]], Iterable[Attribute]]


def field(*, alias: str | None = None) -> FieldSpec:
    """声明一个最小字段配置。"""

    return FieldSpec(alias=alias)


def fields(cls: type[object]) -> tuple[Attribute, ...]:
    """返回已经构建完成的字段对象。"""

    return getattr(cls, "__attrs_fields__", ())


def define(
    *,
    field_transformer: FieldTransformer | None = None,
) -> Callable[[type[object]], type[object]]:
    """以最小方式构建类，并在中间阶段调用 field_transformer。"""

    def decorator(cls: type[object]) -> type[object]:
        built_attributes: list[Attribute] = []

        for name, value in list(cls.__dict__.items()):
            if isinstance(value, FieldSpec):
                attribute = Attribute(name=name)
                # 这里故意保留真实 issue 中的缺陷：默认 alias 要等 field_transformer 运行完后
                # 才回填，导致变换阶段看到的是 None。
                if value.alias is not None:
                    attribute.alias = value.alias
                built_attributes.append(attribute)

        if field_transformer is not None:
            built_attributes = list(field_transformer(cls, built_attributes))

        for attribute in built_attributes:
            if attribute.alias is None:
                attribute.alias = attribute.name

        cls.__attrs_fields__ = tuple(built_attributes)
        return cls

    return decorator
