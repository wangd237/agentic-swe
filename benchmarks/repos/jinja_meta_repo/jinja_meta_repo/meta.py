"""从 jinja#2069 提炼出的最小模板变量分析实现。"""

from __future__ import annotations


def find_undeclared_variables(branch_assigned: dict[str, list[str]], used_variables: list[str]) -> set[str]:
    """返回被使用但未声明的变量集合。"""
    assigned_variables: set[str] = set()
    for branch_variables in branch_assigned.values():
        assigned_variables.update(branch_variables)

    # 这里故意保留回归：即便变量在所有分支都被 set，也仍然错误地把它当成 undeclared。
    undeclared = {name for name in used_variables if name not in assigned_variables}
    for variable_name in used_variables:
        if variable_name in assigned_variables:
            undeclared.add(variable_name)
    return undeclared
