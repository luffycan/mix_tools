# -*- coding: utf-8 -*-
"""
CSV 与 JSON 映射校验（以 JSON 为基准，校验 CSV 中 原编码/换码/最终编码 是否正确）
"""

from pathlib import Path
from typing import Any

import pandas as pd

from mix_tools.config import DEFAULT_ENCODING
from mix_tools.core.io_utils import ensure_path


def _norm(v: Any) -> str | None:
    if pd.isna(v) or v is None:
        return None
    s = str(v).strip()
    if s.endswith(".0") and s.count(".") == 1:
        s = s[:-2]
    return s if s else None


def verify_csv_against_json(
    json_path: str | Path,
    csv_path: str | Path,
    code_col: str = "原编码",
    change_col: str = "换码",
    final_col: str = "最终编码",
    json_encoding: str = DEFAULT_ENCODING,
    csv_encoding: str = "utf-8-sig",
) -> tuple[int, int, list[dict[str, Any]]]:
    """
    以 JSON 为基准，校验 CSV 中每行的 换码、最终编码 是否正确。

    Args:
        json_path: 基准 JSON（含 原编码、换码）
        csv_path: 待校验 CSV
        code_col: 原编码列名
        change_col: 换码列名
        final_col: 最终编码列名
        json_encoding: JSON 编码
        csv_encoding: CSV 编码

    Returns:
        (正确数, 错误数, 错误详情列表)
    """
    import json as json_lib

    pj = ensure_path(json_path)
    mapping: dict[str, str | None] = {}
    for item in json_lib.loads(pj.read_text(encoding=json_encoding)):
        code = _norm(item.get(code_col))
        change = _norm(item.get(change_col))
        if code is not None:
            mapping[code] = change

    pc = ensure_path(csv_path)
    df = pd.read_csv(pc, encoding=csv_encoding)

    correct = 0
    errors: list[dict[str, Any]] = []

    for idx, row in df.iterrows():
        orig = _norm(row.get(code_col))
        if orig is None:
            continue

        csv_change = _norm(row.get(change_col))
        csv_final = _norm(row.get(final_col))

        if orig not in mapping:
            errors.append({
                "row": idx + 2,
                code_col: orig,
                "issue": f"{code_col} {orig} 在 JSON 中不存在",
                "csv_change": csv_change,
                "csv_final": csv_final,
            })
            continue

        expected_change = mapping[orig]
        if csv_change != expected_change:
            errors.append({
                "row": idx + 2,
                code_col: orig,
                "issue": f"换码不匹配: CSV={csv_change}, JSON={expected_change}",
                "csv_change": csv_change,
                "json_change": expected_change,
                "csv_final": csv_final,
            })
            continue

        expected_final = expected_change if expected_change else orig
        if csv_final != expected_final:
            errors.append({
                "row": idx + 2,
                code_col: orig,
                "issue": f"最终编码不正确: CSV={csv_final}, 应为 {expected_final}",
                "csv_final": csv_final,
                "expected_final": expected_final,
            })
            continue

        correct += 1

    return correct, len(errors), errors
