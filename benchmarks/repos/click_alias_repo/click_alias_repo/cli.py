"""从 click#2402 提炼出的最小命令解析实现。"""

from __future__ import annotations


class Command:
    """最小命令对象，只保留 name。"""

    def __init__(self, name: str) -> None:
        self.name = name


class Group:
    """最小命令组，实现底层解析语义。"""

    def __init__(self, commands: dict[str, Command]) -> None:
        self.commands = commands

    def resolve_command(self, cmd_name: str | None) -> tuple[str | None, Command | None, list[str]]:
        if cmd_name is None:
            return None, None, []

        command = self.commands.get(cmd_name)
        if command is None:
            return None, None, []

        return cmd_name, command, []


class AliasedGroup(Group):
    """模拟文档示例里的 alias group。"""

    def resolve_command(self, cmd_name: str | None) -> tuple[str | None, Command | None, list[str]]:
        resolved_name, cmd, args = super().resolve_command(cmd_name)

        # 这里故意保留真实 issue 中的缺陷：cmd 为 None 时仍直接访问 name。
        return cmd.name, cmd, args
