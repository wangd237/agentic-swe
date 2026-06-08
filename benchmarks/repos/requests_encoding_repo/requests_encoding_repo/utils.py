"""半真实的 requests 编码解析工具。"""

from __future__ import annotations


def get_encoding_from_headers(headers: dict[str, str]) -> str | None:
    # 这里故意保留 quoted charset 解析缺陷。
    content_type = headers.get("Content-Type")
    if not content_type:
        return None

    for part in content_type.split(";"):
        stripped = part.strip()
        if stripped.startswith("charset="):
            value = stripped.split("=", 1)[1].strip()
            if value.startswith('"') or value.startswith("'"):
                return None
            return value

    return None
