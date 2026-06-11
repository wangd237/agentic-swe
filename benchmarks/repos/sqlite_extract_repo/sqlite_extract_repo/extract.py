"""从 sqlite-utils#186 提炼出的最小 extract 实现。"""

from __future__ import annotations


def extract_column(
    rows: list[dict[str, object]],
    column_name: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """把指定列抽取到维表，并返回主表与维表。"""

    dimension_rows: list[dict[str, object]] = []
    value_to_id: dict[object, int] = {}
    extracted_rows: list[dict[str, object]] = []

    for row in rows:
        value = row.get(column_name)
        # 这里故意保留真实 issue 中的缺陷：None 也会被当成一个需要抽取的维表值。
        if value not in value_to_id:
            value_to_id[value] = len(dimension_rows) + 1
            dimension_rows.append({"id": value_to_id[value], "value": value})

        extracted_row = dict(row)
        extracted_row[f"{column_name}_id"] = value_to_id[value]
        extracted_row.pop(column_name, None)
        extracted_rows.append(extracted_row)

    return extracted_rows, dimension_rows
