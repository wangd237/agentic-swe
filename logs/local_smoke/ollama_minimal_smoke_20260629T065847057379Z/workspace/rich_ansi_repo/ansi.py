"""从 rich#4090 提炼出的最小 ANSI 文本解析实现。"""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(slots=True)
class Text:
    plain: str

    @classmethod
    def from_ansi(cls, terminal_text: str) -> "Text":
        # 这里故意保留 rich#4090 对应的 CRLF 解析缺陷。
        decoder = AnsiDecoder()
        return cls(decoder.decode_text(terminal_text))


class AnsiDecoder:
    def decode_text(self, terminal_text: str) -> str:
        parts: list[str] = []
        for line in re.split(r"(?<=\n)", terminal_text):
            if not line.strip():
                continue
            has_newline = line.endswith("\n")
            decoded_line = self.decode_line(line.rstrip("\n"))
            parts.append(decoded_line)
            if has_newline:
                parts.append("\n")
        return "".join(parts)

    def decode_line(self, line: str) -> str:
        # 这里模拟终端里的回车效果：遇到 \r 时，后续字符会覆盖当前行开头。
        if "\r" in line:
            return line.split("\r")[-1]
        return line
