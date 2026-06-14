"""从 rich#2411 提炼出的最小 Windows-like 编码回归实现。"""

from __future__ import annotations


RULE_CHAR = "─"


def _safe_text_for_encoding(text: str, encoding: str | None) -> str:
    """在旧编码输出流上，把不可编码字符降级成稳定 ASCII。"""

    if not encoding:
        return text

    try:
        text.encode(encoding)
        return text
    except (LookupError, UnicodeEncodeError):
        # 当前只压缩 rich#2411 的最小问题面：box-drawing 横线在旧编码上不可写出。
        fallback_text = text.replace(RULE_CHAR, "-")
        try:
            fallback_text.encode(encoding)
            return fallback_text
        except (LookupError, UnicodeEncodeError):
            return text.encode(encoding, errors="replace").decode(encoding)


class Console:
    """只保留 rich#2411 所需的最小输出语义。"""

    def __init__(self, *, file: object) -> None:
        self.file = file

    def _write(self, text: str) -> None:
        encoding = getattr(self.file, "encoding", None)
        safe_text = _safe_text_for_encoding(text, encoding)
        self.file.write(safe_text)

    def rule(self, title: str | None = None) -> None:
        rule_text = RULE_CHAR * 10
        if title:
            rule_text = f"{RULE_CHAR * 3} {title} {RULE_CHAR * 3}"
        self._write(f"{rule_text}\n")

    def print(self, text: str) -> None:
        self._write(str(text))
