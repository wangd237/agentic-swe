"""LLM tool 定义。"""

from __future__ import annotations

from typing import Any

_SINGLE_SOURCE_DATA: list[dict[str, Any]] = [
        {
            "name": "list_files",
            "handler_name": "_handle_list_files",
            "risk_level": "read",
            "description": "列出当前仓库中的文件，帮助快速了解项目结构。",
            "is_read_only": True,
            "is_concurrency_safe": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "recursive": {
                        "type": "boolean",
                        "description": "是否递归列出全部文件。",
                        "default": True,
                    }
                },
            },
        },
        {
            "name": "search_graph",
            "handler_name": "_handle_search_graph",
            "risk_level": "read",
            "description": "搜索代码结构图，返回符号（函数/类/方法/变量）的定义位置及置信度。优先于 grep 使用。",
            "is_read_only": True,
            "is_concurrency_safe": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "symbol_name": {
                        "type": "string",
                        "description": "符号名称，例如 'Option' 或 '_bind_to_schema'。子串匹配即可，不需要前后加 .* 正则包裹。",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最多返回的结果数。",
                        "default": 10,
                    },
                },
                "required": ["symbol_name"],
            },
        },
        {
            "name": "search_code",
            "handler_name": "_handle_search_code",
            "risk_level": "read",
            "description": "精确字符串搜索，返回路径、行号及 Python 所属类/函数。可使用 path_prefix/glob 缩小范围，按需扩大。",
            "is_read_only": True,
            "is_concurrency_safe": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "要搜索的代码关键字、接口路径或错误文本。",
                    },
                    "glob": {
                        "type": "string",
                        "description": "可选文件模式，例如 *.py 或 tests/*.py。",
                    },
                    "path_prefix": {
                        "type": "string",
                        "description": "可选仓库相对目录/文件路径，如 app/agent；优先搜索已知候选目录。",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最多返回的匹配行数；命中总数仍会统计。",
                        "minimum": 1,
                        "default": 50,
                        "maximum": 200,
                    },
                },
                "required": ["query"],
            },
        },
        {
            "name": "grep",
            "handler_name": "_handle_grep",
            "risk_level": "read",
            "description": "使用正则搜索代码，返回 file:line 及所属类/函数范围；支持 path_prefix/glob 缩小搜索范围。",
            "is_read_only": True,
            "is_concurrency_safe": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Python re 兼容的正则表达式。",
                    },
                    "glob": {
                        "type": "string",
                        "description": "可选文件过滤，例如 *.py 或 tests/*.py。",
                    },
                    "path_prefix": {
                        "type": "string",
                        "description": "可选仓库相对目录/文件路径，限定搜索子树。",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "最多返回的匹配行数。",
                        "default": 20,
                        "maximum": 200,
                    },
                },
                "required": ["pattern"],
            },
        },
        {
            "name": "read_file",
            "handler_name": "_handle_read_file",
            "risk_level": "read",
            "description": "读取指定文件内容，适合查看代码、测试或配置文件；定位到失败行后优先使用 start_line/end_line 读取局部上下文；截断时按 next_start_line/next_start_char 续读。",
            "is_read_only": True,
            "is_concurrency_safe": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "relative_path": {
                        "type": "string",
                        "description": "仓库内的相对路径。",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "最多返回的字符数。",
                        "default": 6000,
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "可选，按 1 开始的起始行号；适合围绕测试失败位置读取局部代码。",
                        "minimum": 1,
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "可选，按 1 开始的结束行号，必须大于等于 start_line。",
                        "minimum": 1,
                    },
                    "start_char": {
                        "type": "integer",
                        "description": "可选，首行从第几个字符开始（0-based），用于继续读取超长单行；按 next_start_char 续读。",
                        "minimum": 0,
                        "default": 0,
                    },
                },
                "required": ["relative_path"],
            },
        },
        {
            "name": "run_tests",
            "handler_name": "_handle_run_tests",
            "risk_level": "execute",
            "description": "执行任务自带的测试命令，观察失败信息或确认修复是否成功。",
            "is_read_only": False,
            "is_concurrency_safe": False,
            "input_schema": {
                "type": "object",
                "properties": {
                    "timeout_sec": {
                        "type": "integer",
                        "description": "超时时间，单位秒。",
                        "default": 120,
                    },
                },
            },
        },
        {
            "name": "python_repl",
            "handler_name": "_handle_python_repl",
            "risk_level": "execute",
            "description": "受控 Python 单表达式求值工具，用于查询第三方库对象行为；不允许 import、分号、多行、dunder 或文件操作。",
            "is_read_only": False,
            "is_concurrency_safe": False,
            "input_schema": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "单行 Python 表达式，例如 Version('1.0+local').base_version。",
                    },
                },
                "required": ["expression"],
            },
        },
        {
            "name": "write_file",
            "handler_name": "_handle_write_file",
            "risk_level": "modify",
            "description": "覆写仓库内文件内容，用于写入 patch 后的完整文件。",
            "is_read_only": False,
            "is_concurrency_safe": False,
            "input_schema": {
                "type": "object",
                "properties": {
                    "relative_path": {
                        "type": "string",
                        "description": "仓库内的相对路径。",
                    },
                    "content": {
                        "type": "string",
                        "description": "写入后的完整文件内容。",
                    },
                    "localization_override_reason": {
                        "type": "string",
                        "description": "可选；仅当目标文件不在定位候选中但必须修改时填写，说明具体证据和原因。",
                    },
                },
                "required": ["relative_path", "content"],
            },
        },
        {
            "name": "edit_file",
            "handler_name": "_handle_edit_file",
            "risk_level": "modify",
            "description": "通过精确 old_string/new_string 替换编辑仓库内文件，适合小范围修改。",
            "is_read_only": False,
            "is_concurrency_safe": False,
            "input_schema": {
                "type": "object",
                "properties": {
                    "relative_path": {
                        "type": "string",
                        "description": "仓库内的相对路径。",
                    },
                    "old_string": {
                        "type": "string",
                        "description": "要替换的精确原文，必须包含足够上下文以保证唯一匹配。",
                    },
                    "new_string": {
                        "type": "string",
                        "description": "替换后的新文本。",
                    },
                    "localization_override_reason": {
                        "type": "string",
                        "description": "可选；仅当目标文件不在定位候选中但必须修改时填写，说明具体证据和原因。",
                    },
                },
                "required": ["relative_path", "old_string", "new_string"],
            },
        },
        {
            "name": "show_diff",
            "handler_name": "_handle_show_diff",
            "risk_level": "read",
            "description": "查看当前 workspace 相对原始仓库的 diff。",
            "is_read_only": True,
            "is_concurrency_safe": True,
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        },
        {
            "name": "undo",
            "handler_name": "_handle_undo",
            "risk_level": "modify",
            "description": "回滚最近一次 write_file 或 edit_file 写操作影响的文件。",
            "is_read_only": False,
            "is_concurrency_safe": False,
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        },
    ]


def build_tool_definitions() -> list[dict]:
    """Return model-facing schemas derived from the central tool registry."""
    from app.tools.registry import get_tool_registry

    return get_tool_registry().model_definitions()


def read_only_tool_names() -> set[str]:
    return {tool["name"] for tool in _SINGLE_SOURCE_DATA if tool.get("is_read_only")}


def write_tool_names() -> set[str]:
    """Return tool names that modify the workspace."""
    return {"write_file", "edit_file"}


def concurrency_safe_tool_names() -> set[str]:
    return {tool["name"] for tool in _SINGLE_SOURCE_DATA if tool.get("is_concurrency_safe")}
