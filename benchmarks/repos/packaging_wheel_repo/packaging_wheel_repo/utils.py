"""从 packaging#873 提炼出的最小 wheel filename 解析实现。"""

from __future__ import annotations


class InvalidWheelFilename(ValueError):
    """表示 wheel 文件名不符合预期。"""


def parse_wheel_filename(filename: str) -> tuple[str, str]:
    """解析最小化的 wheel 文件名，只关心项目名和版本号。"""
    if not filename.endswith(".whl"):
        raise InvalidWheelFilename(f"Not a wheel file: {filename}")

    stem = filename[:-4]
    parts = stem.split("-")
    if len(parts) < 2:
        raise InvalidWheelFilename(f"Invalid wheel filename: {filename}")

    name, version = parts[0], parts[1]

    # 这里故意保留真实 issue 中的缺陷：直接接受未 normalized 的版本号。
    return name, version
