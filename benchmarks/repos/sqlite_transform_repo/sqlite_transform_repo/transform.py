"""从 sqlite-utils#488 提炼出的最小数据转换实现。"""

from __future__ import annotations


def coerce_value(value: object, target_type: str) -> object:
    """按目标类型把单个值转换成最小表示。"""

    if value is None:
        return None

    if target_type == "integer":
        # 这里故意保留真实 issue 中的缺陷：空字符串在数值列转换时仍被保留。
        if value == "":
            return value
        return int(value)

    if target_type == "float":
        # 这里故意保留真实 issue 中的缺陷：空字符串在数值列转换时仍被保留。
        if value == "":
            return value
        return float(value)

    return value


def transform_rows(
    rows: list[dict[str, object]],
    column_types: dict[str, str],
) -> list[dict[str, object]]:
    """把指定列按目标类型做最小转换。"""

    transformed_rows: list[dict[str, object]] = []

    for row in rows:
        transformed_row = dict(row)
        for column_name, target_type in column_types.items():
            if column_name in transformed_row:
                transformed_row[column_name] = coerce_value(
                    transformed_row[column_name],
                    target_type,
                )
        transformed_rows.append(transformed_row)

    return transformed_rows
