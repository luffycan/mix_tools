# -*- coding: utf-8 -*-
"""
重复数据检测与处理
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from mix_tools.config import DEFAULT_ENCODING
from mix_tools.core.io_utils import ensure_path


def _normalize_value(val: Any) -> Any:
    """去除 pandas 产生的 .0 后缀等"""
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    if s.endswith(".0") and s.count(".") == 1 and s[:-2].isdigit():
        return s[:-2]
    return s


def find_duplicates_in_json(
    json_path: str | Path,
    key_column: str = "原编码",
    encoding: str = DEFAULT_ENCODING,
) -> dict[str, list[dict[str, Any]]]:
    """
    在 JSON 数组中按指定键找重复项。

    Args:
        json_path: JSON 文件路径
        key_column: 作为去重键的列名
        encoding: 编码

    Returns:
        {重复键: [该键对应的所有记录], ...}
    """
    p = ensure_path(json_path)
    data = json.loads(p.read_text(encoding=encoding))
    df = pd.DataFrame(data)

    if key_column not in df.columns:
        return {}

    dup_mask = df.duplicated(subset=[key_column], keep=False)
    dup_df = df[dup_mask]
    result: dict[str, list[dict[str, Any]]] = {}

    for key, group in dup_df.groupby(key_column):
        result[str(key)] = group.to_dict("records")

    return result


def find_complete_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """查找完全重复的行"""
    return df[df.duplicated(keep=False)]


def find_duplicates_by_column(
    df: pd.DataFrame,
    subset: list[str],
) -> pd.DataFrame:
    """按指定列组合查找重复行"""
    return df[df.duplicated(subset=subset, keep=False)]


def filter_json_dedup(
    json_path: str | Path,
    output_path: str | Path,
    key_columns: list[str] | None = None,
    keep_columns: list[str] | None = None,
    encoding: str = DEFAULT_ENCODING,
) -> int:
    """
    对 JSON 去重并写出。可指定键列和保留列。

    Args:
        json_path: 输入 JSON
        output_path: 输出 JSON
        key_columns: 去重键，默认 ['原编码']
        keep_columns: 保留的列，None 表示全部
        encoding: 编码

    Returns:
        去重后的记录数
    """
    p = ensure_path(json_path)
    data = json.loads(p.read_text(encoding=encoding))
    df = pd.DataFrame(data)

    key_cols = key_columns or ["原编码"]
    if not all(c in df.columns for c in key_cols):
        raise ValueError(f"缺少列: {key_cols}")

    df = df.drop_duplicates(keep="first")
    df = df.drop_duplicates(subset=key_cols, keep="first")

    if keep_columns:
        df = df[[c for c in keep_columns if c in df.columns]]

    records = df.to_dict("records")
    out = Path(output_path) if isinstance(output_path, str) else Path(output_path)
    out.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding=encoding)
    return len(records)


def check_csv_duplicates(
    csv_path: str | Path,
    key_column: str = "原编码",
    encoding: str = "utf-8-sig",
) -> tuple[bool, int, int]:
    """
    检查 CSV 中是否存在重复。

    Args:
        csv_path: CSV 文件路径
        key_column: 键列
        encoding: 编码

    Returns:
        (是否无重复, 总行数, 唯一键数)
    """
    p = ensure_path(csv_path)
    df = pd.read_csv(p, encoding=encoding)

    total = len(df)
    unique = df[key_column].nunique()
    has_dup = total != unique
    return (not has_dup, total, unique)
