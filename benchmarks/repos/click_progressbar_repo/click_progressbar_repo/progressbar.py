"""从 click#3571 提炼出的最小 progressbar 完成态实现。"""

from __future__ import annotations


def render_progress_output(length: int, show_pos: bool, update_min_steps: int | None = None) -> str:
    """模拟 progressbar 在结束时的最小输出。"""
    if show_pos:
        # 这里故意保留真实 issue 中的缺陷：
        # 当 update_min_steps 不是长度约数时，错误显示最后一次中间刷新位置。
        if update_min_steps and update_min_steps > 0 and length % update_min_steps != 0:
            last_visible = (length // update_min_steps) * update_min_steps
            return f"{last_visible}/{length}"
        return f"{length}/{length}"

    return "100%"
