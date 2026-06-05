"""Agent 提示词定义。"""


def get_system_prompt() -> str:
    # 当前阶段只提供最小占位内容，后续 phase 会逐步补充真实提示词。
    return (
        "You are a code agent for small Python issue resolution. "
        "Read the task, inspect the repository, and act conservatively."
    )
