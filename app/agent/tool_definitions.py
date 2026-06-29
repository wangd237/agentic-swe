"""LLM tool 定义。"""

from __future__ import annotations


def build_tool_definitions() -> list[dict]:
    """返回给 LLM 的工具 JSON Schema。"""

    return [
        {
            "name": "list_files",
            "description": "列出当前仓库中的文件，帮助快速了解项目结构。",
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
            "name": "search_code",
            "description": "在仓库中搜索代码字符串，用于定位相关函数、测试或错误信息。",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "要搜索的代码关键字或错误文本。",
                    }
                },
                "required": ["query"],
            },
        },
        {
            "name": "grep",
            "description": "使用正则表达式搜索代码，返回 file:line:content 风格的匹配行。",
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
                    "max_results": {
                        "type": "integer",
                        "description": "最多返回的匹配行数。",
                        "default": 20,
                    },
                },
                "required": ["pattern"],
            },
        },
        {
            "name": "read_file",
            "description": "读取指定文件内容，适合查看代码、测试或配置文件；定位到失败行后优先使用 start_line/end_line 读取局部上下文。",
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
                },
                "required": ["relative_path"],
            },
        },
        {
            "name": "run_tests",
            "description": "执行任务自带的测试命令，观察失败信息或确认修复是否成功。",
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
            "description": "受控 Python 单表达式求值工具，用于查询第三方库对象行为；不允许 import、分号、多行、dunder 或文件操作。",
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
            "description": "覆写仓库内文件内容，用于写入 patch 后的完整文件；不要用于创建 debug.py/tmp.py/scratch.py/probe.py 等临时调试文件。",
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
            "description": "通过精确 old_string/new_string 替换编辑仓库内文件，适合小范围修改。",
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
            "description": "查看当前 workspace 相对原始仓库的 diff。",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        },
        {
            "name": "undo",
            "description": "回滚最近一次 write_file 或 edit_file 写操作影响的文件。",
            "input_schema": {
                "type": "object",
                "properties": {},
            },
        },
        {
            "name": "search_graph",
            "description": "Query the codebase graph for symbols matching a name pattern. Returns structured results with file paths, symbol names, and confidence scores. Use this when grep/search_code returns too many results or when you need to understand cross-file call relationships.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name_pattern": {
                        "type": "string",
                        "description": "Regex pattern to match symbol names, e.g. '.*hostname.*' or '_bind_to_schema'.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return.",
                        "default": 10,
                    },
                },
                "required": ["name_pattern"],
            },
        },
    ]
