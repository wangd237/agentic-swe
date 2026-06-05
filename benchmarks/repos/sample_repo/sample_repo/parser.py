"""示例解析模块。"""


def parse_items(items: list[str]) -> list[str]:
    # 这里故意保留一个空输入 bug，供后续 phase 的 Agent 去修复。
    first_item = items[0]
    normalized_items = [first_item.strip().lower()]

    for item in items[1:]:
        normalized_items.append(item.strip().lower())

    return normalized_items
