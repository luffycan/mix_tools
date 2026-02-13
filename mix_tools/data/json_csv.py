# -*- coding: utf-8 -*-
"""
JSON 与 CSV 互转工具
"""

import csv
import json
from pathlib import Path
from typing import Any

from mix_tools.config import DEFAULT_ENCODING
from mix_tools.core.io_utils import ensure_path


def json_to_csv(
    json_path: str | Path,
    csv_path: str | Path,
    encoding: str = DEFAULT_ENCODING,
    csv_encoding: str = "utf-8-sig",
) -> int:
    """
    将 JSON 数组（字典列表）转换为 CSV。

    Args:
        json_path: 输入 JSON 文件路径
        csv_path: 输出 CSV 文件路径
        encoding: JSON 读取编码
        csv_encoding: CSV 写入编码（默认 utf-8-sig 兼容 Excel）

    Returns:
        转换的记录数
    """
    p = ensure_path(json_path)
    data = json.loads(p.read_text(encoding=encoding))

    if not data:
        out = Path(csv_path) if isinstance(csv_path, str) else csv_path
        out.write_text("", encoding=csv_encoding)
        return 0

    fieldnames = list(data[0].keys())
    out = Path(csv_path) if isinstance(csv_path, str) else Path(csv_path)

    with out.open("w", encoding=csv_encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            processed = {k: (v if v is not None else "") for k, v in row.items()}
            writer.writerow(processed)

    return len(data)


def csv_to_json(
    csv_path: str | Path,
    json_path: str | Path,
    encoding: str = "utf-8-sig",
    json_encoding: str = DEFAULT_ENCODING,
) -> int:
    """
    将 CSV 转换为 JSON 数组。

    Args:
        csv_path: 输入 CSV 文件路径
        json_path: 输出 JSON 文件路径
        encoding: CSV 读取编码
        json_encoding: JSON 写入编码

    Returns:
        转换的记录数
    """
    import pandas as pd

    p = ensure_path(csv_path)
    df = pd.read_csv(p, encoding=encoding)

    records: list[dict[str, Any]] = df.fillna("").astype(str).to_dict("records")

    # 还原空字符串为 None（可选，保持与 json_to_csv 对称）
    out = Path(json_path) if isinstance(json_path, str) else Path(json_path)
    out.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding=json_encoding,
    )
    return len(records)
