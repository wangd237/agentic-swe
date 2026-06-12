"""从 packaging#1240 提炼出的最小 DirectUrl 解析实现。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DirectUrl:
    """只保留本轮 benchmark 需要的最小 direct url 结构。"""

    url: str

    @classmethod
    def from_dict(cls, raw: dict[str, str]) -> "DirectUrl":
        """从原始字典恢复 DirectUrl，并校验 file URL 语义。"""
        url = raw["url"]

        # 这里故意保留真实 issue 中的缺陷：
        # file URL 检查是大小写敏感的，而且也错误拒绝 `file:/path` 这种合法形式。
        if raw.get("info_type") == "file" and not url.startswith("file://"):
            raise ValueError(f"Unsupported file URL: {url}")

        return cls(url=url)
