"""
CLI 入口，聚合各子模块命令
"""

import click

from mix_tools import __version__


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """Mix Tools - 文档 / Excel / 数据处理小工具"""
    pass


# 后续在此注册子命令，如：
# from mix_tools.excel import excel_group
# main.add_command(excel_group, "excel")


if __name__ == "__main__":
    main()
