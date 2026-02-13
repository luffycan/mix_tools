# -*- coding: utf-8 -*-
"""
根据文本文件生成批量 INSERT SQL
"""

from pathlib import Path
from typing import Callable

from mix_tools.config import DEFAULT_ENCODING
from mix_tools.core.io_utils import ensure_path
from mix_tools.data.dedup import read_lines


def generate_insert_sql(
    input_path: str | Path,
    output_path: str | Path,
    table: str = "hibox_orders.device_need_sync_order",
    columns: tuple[str, ...] = ("deviceCode", "remark", "createTime"),
    remark: str = "1543155712-成都吖吖便利",
    ignore_duplicate: bool = True,
    encoding: str = DEFAULT_ENCODING,
    value_fn: Callable[[str], str] | None = None,
) -> int:
    """
    从文件每行读取一个编码，生成批量 INSERT 语句。

    Args:
        input_path: 输入文件（每行一个编码）
        output_path: 输出 SQL 文件
        table: 表名（含库名）
        columns: 列名
        remark: 备注列默认值
        ignore_duplicate: 是否使用 INSERT IGNORE
        encoding: 编码
        value_fn: 自定义每行到值的映射，默认 (code, remark, NOW())

    Returns:
        插入的记录数
    """
    codes = read_lines(input_path, encoding)
    if not codes:
        out = Path(output_path) if isinstance(output_path, str) else Path(output_path)
        out.write_text("-- 无数据\n", encoding=encoding)
        return 0

    if value_fn:
        values = [value_fn(c) for c in codes]
    else:
        values = [f"('{c}','{remark}',NOW())" for c in codes]

    sql = f"INSERT {'IGNORE ' if ignore_duplicate else ''}INTO {table} ({','.join(columns)}) VALUES {','.join(values)};"
    out = Path(output_path) if isinstance(output_path, str) else Path(output_path)
    out.write_text(sql + "\n", encoding=encoding)
    return len(codes)
