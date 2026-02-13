# -*- coding: utf-8 -*-
"""
设备统计工具函数
"""

import gzip
from pathlib import Path


def open_json_or_gz(path: str | Path):
    """支持 .json 或 .json.gz，返回文本模式的文件对象"""
    path = Path(path)
    if path.suffix == ".gz" or path.name.endswith(".json.gz"):
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open(encoding="utf-8")
