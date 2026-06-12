"""从 tomlkit#505 提炼出的最小 out-of-order table 访问实现。"""

from __future__ import annotations

from dataclasses import dataclass


class KeyAlreadyPresent(Exception):
    """模拟 tomlkit 在代理重建阶段抛出的重复键异常。"""


@dataclass(frozen=True)
class ParsedHooksDocument:
    """保存 `hooks` 节点下的重复 array table 与同级子表。"""

    repeated_tables: dict[str, list[dict[str, object]]]
    sibling_tables: dict[str, object]


class _ProxyContainer:
    """最小容器，负责模拟 tomlkit 的底层 raw append 约束。"""

    def __init__(self) -> None:
        self._items: dict[str, object] = {}

    def raw_append(self, key: str, value: object) -> None:
        if key in self._items:
            raise KeyAlreadyPresent(f'Key "{key}" already exists.')
        self._items[key] = value

    def export(self) -> dict[str, object]:
        return dict(self._items)


class OutOfOrderTableProxy:
    """最小代理对象，只保留本轮 benchmark 需要的访问语义。"""

    def __init__(self, data: dict[str, object]) -> None:
        self._data = data

    @classmethod
    def from_hooks(cls, hooks_doc: ParsedHooksDocument) -> "OutOfOrderTableProxy":
        """把解析后的 hooks 节点重建成代理视图。"""
        internal = _ProxyContainer()

        # 这里故意保留真实 issue 中的缺陷：
        # 当存在同名 repeated array table 且还有同级子表时，错误逐条 raw_append，
        # 结果在第二次写入 `Stop` 时触发 KeyAlreadyPresent。
        if hooks_doc.sibling_tables:
            for table_name, entries in hooks_doc.repeated_tables.items():
                for entry in entries:
                    internal.raw_append(table_name, entry)
        else:
            for table_name, entries in hooks_doc.repeated_tables.items():
                internal.raw_append(table_name, list(entries))

        for table_name, table_value in hooks_doc.sibling_tables.items():
            internal.raw_append(table_name, table_value)

        return cls(internal.export())

    def to_dict(self) -> dict[str, object]:
        """返回稳定字典，便于测试直接断言。"""
        return dict(self._data)


class ParsedDocument:
    """最小解析结果对象。"""

    def __init__(self, sections: dict[str, object]) -> None:
        self._sections = sections

    def get(self, key: str) -> object | None:
        value = self._sections.get(key)
        if isinstance(value, ParsedHooksDocument):
            return OutOfOrderTableProxy.from_hooks(value).to_dict()
        return value


def _parse_assignment(line: str) -> tuple[str, str]:
    """解析最小 key=value 赋值行。"""
    key, raw_value = [part.strip() for part in line.split("=", 1)]
    return key, raw_value.strip('"')


def parse_document(text: str) -> ParsedDocument:
    """解析本轮 benchmark 需要的最小 TOML 子集。"""
    stop_entries: list[dict[str, object]] = []
    state_table: dict[str, object] = {}
    current_stop: dict[str, object] | None = None
    current_stop_hook: dict[str, object] | None = None
    in_state_example = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line == "[hooks]":
            current_stop = None
            current_stop_hook = None
            in_state_example = False
            continue

        if line == "[[hooks.Stop]]":
            current_stop = {"hooks": []}
            stop_entries.append(current_stop)
            current_stop_hook = None
            in_state_example = False
            continue

        if line == "[[hooks.Stop.hooks]]":
            if current_stop is None:
                raise ValueError("hooks.Stop.hooks 必须出现在 hooks.Stop 之后。")
            current_stop_hook = {}
            hooks_list = current_stop.setdefault("hooks", [])
            assert isinstance(hooks_list, list)
            hooks_list.append(current_stop_hook)
            in_state_example = False
            continue

        if line == "[hooks.state]":
            current_stop = None
            current_stop_hook = None
            in_state_example = False
            continue

        if line == "[hooks.state.example]":
            state_table.setdefault("example", {})
            current_stop = None
            current_stop_hook = None
            in_state_example = True
            continue

        if "=" not in line:
            continue

        key, value = _parse_assignment(line)
        if current_stop_hook is not None:
            current_stop_hook[key] = value
            continue

        if current_stop is not None:
            current_stop[key] = value
            continue

        if in_state_example:
            example_table = state_table.setdefault("example", {})
            assert isinstance(example_table, dict)
            example_table[key] = value

    hooks_doc = ParsedHooksDocument(
        repeated_tables={"Stop": stop_entries} if stop_entries else {},
        sibling_tables={"state": state_table} if state_table else {},
    )
    return ParsedDocument({"hooks": hooks_doc})
