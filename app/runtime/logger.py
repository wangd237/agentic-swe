"""日志写入辅助函数。"""

import json
from pathlib import Path
from typing import Any


def write_json(path: str | Path, payload: Any) -> None:
    # 统一 JSON 写入方式，后续 trace / result / metadata 都可复用。
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump(mode="json")
    elif hasattr(payload, "to_dict"):
        payload = payload.to_dict()
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def write_text(path: str | Path, content: str) -> None:
    # 保持文本落盘入口简单稳定，便于后续写 summary 和调试信息。
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
