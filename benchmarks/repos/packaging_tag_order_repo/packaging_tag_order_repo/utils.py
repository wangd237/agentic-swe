"""从 packaging#909 提炼出的最小 wheel tag 顺序校验实现。"""

from __future__ import annotations


class InvalidWheelFilename(ValueError):
    """表示 wheel 文件名不符合预期。"""


def parse_wheel_filename(filename: str) -> tuple[str, str, str]:
    """解析最小化的 wheel 文件名，只关心项目名、版本号和 python tag。"""
    if not filename.endswith(".whl"):
        raise InvalidWheelFilename(f"Not a wheel file: {filename}")

    stem = filename[:-4]
    parts = stem.split("-")
    if len(parts) < 5:
        raise InvalidWheelFilename(f"Invalid wheel filename: {filename}")

    name, version, python_tag = parts[0], parts[1], parts[2]

    # 这里故意保留真实 issue 中的缺陷：
    # 当前实现只拆出 compressed python tag，但没有校验它们是否已经排序。
    compressed_tags = python_tag.split(".")
    if not compressed_tags:
        raise InvalidWheelFilename(f"Invalid python tag: {filename}")

    return name, version, python_tag
