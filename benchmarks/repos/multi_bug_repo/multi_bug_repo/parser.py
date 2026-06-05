"""包含多种缺陷模式的解析模块。"""


def parse_items(items: list[str | None]) -> list[str]:
    # 这里故意同时保留空输入和 None 元素处理缺陷。
    first_item = items[0]
    normalized_items = [first_item.strip().lower()]

    for item in items[1:]:
        normalized_items.append(item.strip().lower())

    return normalized_items
