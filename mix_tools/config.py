"""
配置加载，支持环境变量与本地配置
"""

from pathlib import Path

# 默认编码
DEFAULT_ENCODING = "utf-8"

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
