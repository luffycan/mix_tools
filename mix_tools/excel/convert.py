# -*- coding: utf-8 -*-
"""
Excel 转换：Excel -> JSON，设备映射 CSV 生成
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from mix_tools.config import DEFAULT_ENCODING
from mix_tools.core.io_utils import ensure_path


def _remove_trailing_zero(val: Any) -> Any:
    """去除字符串末尾的 .0"""
    if pd.isna(val) or val is None:
        return None
    s = str(val).strip()
    if s.endswith(".0") and s.count(".") == 1:
        return s[:-2]
    return s


def excel_to_json(
    excel_path: str | Path,
    output_path: str | Path,
    sheet_name: str | int = 0,
    encoding: str = DEFAULT_ENCODING,
) -> int:
    """
    将 Excel 指定 Sheet 转为 JSON 数组。

    Args:
        excel_path: Excel 文件路径
        output_path: 输出 JSON 路径
        sheet_name: Sheet 名或索引
        encoding: JSON 写入编码

    Returns:
        记录数
    """
    p = ensure_path(excel_path)
    df = pd.read_excel(p, sheet_name=sheet_name)
    df = df.astype(str).replace("nan", None)

    for col in df.columns:
        df[col] = df[col].apply(_remove_trailing_zero)

    records = df.to_dict("records")
    out = Path(output_path) if isinstance(output_path, str) else Path(output_path)
    out.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding=encoding,
    )
    return len(records)


def read_lines_multi_encoding(path: str | Path) -> tuple[list[str], str]:
    """
    尝试多种编码读取文件行。用于设备清单等可能 GBK 的文件。

    Returns:
        (行列表, 实际使用的编码)
    """
    encodings = ["utf-8", "utf-8-sig", "utf-16", "utf-16-le", "gbk", "gb18030", "mbcs"]
    p = Path(path) if isinstance(path, str) else Path(path)

    for enc in encodings:
        try:
            text = p.read_text(encoding=enc)
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            if lines:
                return lines, enc
        except Exception:
            continue

    raw = p.read_bytes()
    for enc in encodings:
        try:
            text = raw.decode(enc, errors="ignore")
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            if lines:
                return lines, enc
        except Exception:
            continue

    raise ValueError(f"无法用任何编码读取: {path}")


def generate_device_mapping_csv(
    device_list_path: str | Path,
    excel_path: str | Path,
    sheet_name: str | int,
    output_csv_path: str | Path,
    code_col: str = "原编码",
    change_col: str = "换码",
    encoding: str = "utf-8-sig",
) -> int:
    """
    根据设备清单和 Excel 映射表，生成 原编码/换码/最终编码 CSV。

    Args:
        device_list_path: 设备编码列表文件（每行一个）
        excel_path: 含 原编码、换码 的 Excel
        sheet_name: Sheet 名或索引
        output_csv_path: 输出 CSV 路径
        code_col: 原编码列名
        change_col: 换码列名
        encoding: CSV 输出编码

    Returns:
        输出行数
    """
    codes, _ = read_lines_multi_encoding(device_list_path)

    p = ensure_path(excel_path)
    df_map = pd.read_excel(p, sheet_name=sheet_name, dtype=str)
    if code_col not in df_map.columns or change_col not in df_map.columns:
        raise ValueError(f"Excel 必须包含 '{code_col}' 和 '{change_col}' 列")

    df_map[code_col] = df_map[code_col].astype(str).str.replace(r"\.0$", "", regex=True)
    df_map[change_col] = df_map[change_col].astype(str).str.replace(r"\.0$", "", regex=True)
    df_map[change_col] = df_map[change_col].replace(
        {"nan": None, "NaN": None, "None": None, "": None}
    )

    df_list = pd.DataFrame({code_col: codes})
    merged = df_list.merge(
        df_map[[code_col, change_col]],
        on=code_col,
        how="left",
    )

    final_col = "最终编码"
    merged[final_col] = merged[change_col]
    merged.loc[
        merged[final_col].isna() | (merged[final_col] == ""),
        final_col,
    ] = merged[code_col]

    merged = merged.drop_duplicates(subset=[code_col], keep="first")
    merged = merged.drop_duplicates(keep="first")

    out = Path(output_csv_path) if isinstance(output_csv_path, str) else Path(output_csv_path)
    merged[[code_col, change_col, final_col]].to_csv(out, index=False, encoding=encoding)
    return len(merged)


# 兼容旧项目直接调用
if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 4:
        excel_path = sys.argv[1]
        sheet_name = sys.argv[2]
        output = sys.argv[3]
        excel_to_json(excel_path, output, sheet_name=sheet_name)
    else:
        print("Usage: python -m mix_tools.excel.convert <excel_path> <sheet_name> <output.json>")
