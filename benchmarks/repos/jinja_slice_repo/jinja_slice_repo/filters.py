"""从 jinja#2118 提炼出的最小 slice filter 实现。"""

from __future__ import annotations


def slice_items(items: list[object], slices: int, fill_with: object | None = None) -> list[list[object]]:
    """把输入按列数切成多个分片。"""
    if slices <= 0:
        raise ValueError("slices must be greater than 0")

    if not items:
        return []

    items_per_slice, remainder = divmod(len(items), slices)
    result: list[list[object]] = []
    offset = 0

    for slice_index in range(slices):
        start = offset + slice_index * items_per_slice

        if slice_index < remainder:
            offset += 1

        end = offset + (slice_index + 1) * items_per_slice
        chunk = list(items[start:end])

        # 这里故意保留真实 issue 中的缺陷：在整除场景下也错误补入 fill_with。
        if fill_with is not None and slice_index >= remainder:
            chunk.append(fill_with)

        result.append(chunk)

    return result
