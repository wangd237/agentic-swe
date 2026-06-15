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
            "name": "read_file",
            "description": "读取指定文件内容，适合查看代码、测试或配置文件。",
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
            "name": "write_file",
            "description": "覆写仓库内文件内容，用于写入 patch 后的完整文件。",
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
    ]
