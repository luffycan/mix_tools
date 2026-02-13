# -*- coding: utf-8 -*-
"""
文件内容对比：读取两文件中的项（行或分隔符拆分），求交集、差集
"""

from pathlib import Path
from typing import Callable

from mix_tools.data.dedup import read_lines
from mix_tools.core.io_utils import ensure_path


def read_items(
    path: str | Path,
    sep: str | None = None,
    normalize: Callable[[str], str] | None = None,
) -> list[str]:
    """
    从文件读取项。若文件中无换行且有 sep，则按 sep 分割；否则按行。

    Args:
        path: 文件路径
        sep: 分隔符，如 ','。若为 None 则仅按行
        normalize: 每项的处理函数，如 strip、转数字等

    Returns:
        去重后的项列表
    """
    p = ensure_path(path)
    content = p.read_text(encoding="utf-8").strip()

    if "\n" not in content and sep and sep in content:
        items = [x.strip() for x in content.split(sep) if x.strip()]
    else:
        items = [line.strip() for line in content.splitlines() if line.strip()]

    if normalize:
        items = [normalize(x) for x in items if x]

    return list(dict.fromkeys(items))


def compare_files(
    path_a: str | Path,
    path_b: str | Path,
    sep: str | None = ",",
) -> tuple[set[str], set[str], set[str]]:
    """
    对比两个文件中的项，求交集与差集。

    Args:
        path_a: 文件 A
        path_b: 文件 B
        sep: 单行多列时的分隔符

    Returns:
        (仅在 A 中, 仅在 B 中, 两文件共有)
    """
    items_a = set(read_items(path_a, sep=sep))
    items_b = set(read_items(path_b, sep=sep))

    only_a = items_a - items_b
    only_b = items_b - items_a
    common = items_a & items_b

    return only_a, only_b, common


def sort_items_numeric(items: set[str]) -> list[str]:
    """按数字大小排序；非数字的放前面按字符串排"""
    def key_fn(x: str) -> tuple[bool, int | str]:
        if x.isdigit():
            return (False, int(x))
        return (True, x)

    return sorted(items, key=key_fn)
