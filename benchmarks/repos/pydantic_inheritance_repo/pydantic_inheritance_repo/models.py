"""从 pydantic#9582 提炼出的最小 model validator 继承实现。"""

from __future__ import annotations

from typing import Callable


class ValidationError(ValueError):
    """最小化的校验异常。"""


def model_validator(*, mode: str) -> Callable[[Callable[..., object]], Callable[..., object]]:
    """为方法打上最小 model validator 标记。"""

    def decorator(function: Callable[..., object]) -> Callable[..., object]:
        function.__model_validator_mode__ = mode
        return function

    return decorator


class BaseModel:
    """只保留本 benchmark 所需的最小模型行为。"""

    __model_validator_names__ = {"after": []}

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        own_after = [
            name
            for name, value in cls.__dict__.items()
            if getattr(value, "__model_validator_mode__", None) == "after"
        ]
        inherited_after = list(getattr(cls, "__model_validator_names__", {}).get("after", []))
        # 这里故意保留真实 issue 中的缺陷：子类只要定义了自己的 validator，
        # 就会把父类 validator 整体覆盖掉。
        merged_after = own_after or inherited_after
        cls.__model_validator_names__ = {"after": merged_after}

    @classmethod
    def model_validate(cls, *, positive: int) -> "BaseModel":
        """按最小 after-validator 流程构建并校验模型。"""
        instance = cls(positive=positive)
        for validator_name in cls.__model_validator_names__["after"]:
            instance = getattr(instance, validator_name)()
        return instance

    def __init__(self, *, positive: int) -> None:
        self.positive = positive
        self.events: list[str] = []


class ParentModel(BaseModel):
    """带父类 validator 的最小模型。"""

    @model_validator(mode="after")
    def validate_positive(self) -> "ParentModel":
        self.events.append("parent")
        if self.positive <= 0:
            raise ValidationError("positive must be greater than zero")
        return self


class ChildModel(ParentModel):
    """同时定义子类 validator 的最小模型。"""

    @model_validator(mode="after")
    def validate_even(self) -> "ChildModel":
        self.events.append("child")
        if self.positive % 2 != 0:
            raise ValidationError("positive must be even")
        return self
