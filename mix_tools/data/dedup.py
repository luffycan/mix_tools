# -*- coding: utf-8 -*-
"""
文本去重工具：按行读取、去重、按指定分隔符输出
"""

from pathlib import Path
from typing import Iterable

from mix_tools.config import DEFAULT_ENCODING
from mix_tools.core.io_utils import ensure_path


def read_lines(path: str | Path, encoding: str = DEFAULT_ENCODING) -> list[str]:
    """从文件按行读取非空行，strip 后返回"""
    p = ensure_path(path)
    return [line.strip() for line in p.read_text(encoding=encoding).splitlines() if line.strip()]


def dedup_preserve_order(items: Iterable[str]) -> list[str]:
    """去重且保持首次出现顺序"""
    seen: set[str] = set()
    unique: list[str] = []
    for x in items:
        if x not in seen:
            seen.add(x)
            unique.append(x)
    return unique


def dedup_file(
    input_path: str | Path,
    output_path: str | Path,
    separator: str = ",",
    encoding: str = DEFAULT_ENCODING,
) -> tuple[int, int]:
    """
    对文件按行去重，输出为单行（用 separator 连接）或按行输出。

    Args:
        input_path: 输入文件
        output_path: 输出文件
        separator: 输出分隔符，空字符串表示每行一个
        encoding: 读写编码

    Returns:
        (原始行数, 去重后行数)
    """
    lines = read_lines(input_path, encoding)
    unique = dedup_preserve_order(lines)

    out = Path(output_path) if isinstance(output_path, str) else Path(output_path)
    if separator:
        out.write_text(separator.join(unique), encoding=encoding)
    else:
        out.write_text("\n".join(unique) + "\n", encoding=encoding)

    return len(lines), len(unique)


def dedup_files_in_dir(
    dir_path: str | Path,
    filenames: list[str],
    output_suffix: str = "_去重",
    separator: str = ",",
    encoding: str = DEFAULT_ENCODING,
) -> list[tuple[str, int, int]]:
    """
    对目录下多个文件分别去重并输出。

    Args:
        dir_path: 目录路径
        filenames: 要处理的文件名列表
        output_suffix: 输出文件名后缀（不含扩展名）
        separator: 输出分隔符
        encoding: 编码

    Returns:
        [(文件名, 原始行数, 去重后行数), ...]
    """
    base = Path(dir_path) if isinstance(dir_path, str) else Path(dir_path)
    results: list[tuple[str, int, int]] = []

    for fname in filenames:
        inp = base / fname
        stem = inp.stem
        ext = inp.suffix
        out_fname = f"{stem}{output_suffix}{ext}"
        out_path = base / out_fname

        orig, uniq = dedup_file(inp, out_path, separator=separator, encoding=encoding)
        results.append((out_fname, orig, uniq))

    return results
