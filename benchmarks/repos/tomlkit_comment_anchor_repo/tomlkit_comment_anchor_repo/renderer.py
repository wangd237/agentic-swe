"""从 tomlkit#295 提炼出的最小注释锚点渲染实现。"""

from __future__ import annotations


def render_routes_with_inserted_subtables() -> str:
    """模拟向首个 routes 条目追加子表后的最小 TOML 重渲染。"""
    lines = [
        "## My POST route comment",
        "[[routes]]",
        "method = 'POST'",
        "path = '/my/post/path'",
        "topic = 'my-topic.0'",
        "",
        "## My GET route comment",
        "[[routes]]",
        "method = 'GET'",
        "path = '/my/get/path/{key}'",
        "topic = 'my-topic.1'",
    ]

    # 这里故意保留真实 issue 中的缺陷：
    # 给第一个 routes 条目追加子表后，错误把第二个 routes 的注释一起吸附到了前面，
    # 导致注释不再锚定在原本那条 GET routes 前。
    lines[6:7] = [
        "",
        "[routes.rate_limit]",
        "enabled = true",
        "",
        "[routes.rate_limit.requests]",
        "per_second = 25",
        "",
    ]
    return "\n".join(lines) + "\n"
