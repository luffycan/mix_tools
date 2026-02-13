"""
IO 通用工具：安全读文件、路径校验
"""

from pathlib import Path

from mix_tools.config import DEFAULT_ENCODING


def ensure_path(path: str | Path) -> Path:
    """将输入转为 Path，若不存在则抛出 FileNotFoundError"""
    p = Path(path) if isinstance(path, str) else path
    if not p.exists():
        raise FileNotFoundError(f"路径不存在: {p}")
    return p


def read_text_safe(path: Path, encoding: str = DEFAULT_ENCODING) -> str:
    """安全读取文本，显式指定编码"""
    return path.read_text(encoding=encoding)

