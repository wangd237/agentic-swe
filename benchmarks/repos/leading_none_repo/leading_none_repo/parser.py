"""包含首元素 None 缺陷的解析模块。"""


def parse_items(items: list[str | None]) -> list[str]:
    # 这里故意保留空输入、首元素 None 和中间 None 的处理缺陷。
    first_item = items[0]
    normalized_items = [first_item.strip().lower()]

    for item in items[1:]:
        normalized_items.append(item.strip().lower())

    return normalized_items
