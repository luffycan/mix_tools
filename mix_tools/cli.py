"""
CLI 入口，聚合各子模块命令
"""

from pathlib import Path

import click

from mix_tools import __version__


@click.group()
@click.version_option(version=__version__)
def main() -> None:
    """Mix Tools - 文档 / Excel / 数据处理小工具"""
    pass


# 数据模块命令
from mix_tools.data.json_csv import json_to_csv as _json_to_csv
from mix_tools.data.json_csv import csv_to_json as _csv_to_json
from mix_tools.data.dedup import dedup_file as _dedup_file
from mix_tools.data.dedup import dedup_files_in_dir as _dedup_files_in_dir
from mix_tools.data.file_compare import compare_files as _compare_files
from mix_tools.data.file_compare import sort_items_numeric as _sort_items_numeric
from mix_tools.data.sql_generate import generate_insert_sql as _generate_insert_sql
from mix_tools.data.duplicates import find_duplicates_in_json as _find_dup_json
from mix_tools.data.duplicates import filter_json_dedup as _filter_json_dedup
from mix_tools.data.duplicates import check_csv_duplicates as _check_csv_dup
from mix_tools.data.verify import verify_csv_against_json as _verify_csv_json
from mix_tools.excel.convert import excel_to_json as _excel_to_json
from mix_tools.excel.convert import generate_device_mapping_csv as _gen_device_csv


def _is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


@main.command("ui")
@click.option("-p", "--port", default=8501, help="端口")
@click.option("--host", default="localhost", help="绑定地址")
def cmd_ui(port: int, host: str) -> None:
    """启动可视化 Web 界面"""
    import subprocess
    import sys

    if _is_port_in_use(port, "127.0.0.1" if host == "localhost" else host):
        click.echo(f"端口 {port} 已被占用，Mix Tools UI 可能已在运行。")
        click.echo(f"请访问 http://localhost:{port} 或先关闭已有进程。")
        raise SystemExit(0)

    app_path = Path(__file__).resolve().parent / "ui" / "app.py"
    try:
        proc = subprocess.run(
            [
                sys.executable, "-m", "streamlit", "run", str(app_path),
                "--server.port", str(port),
                "--server.address", host,
                "--server.headless", "true",
                "--server.portRetries", "0",
            ],
            check=False,
        )
        raise SystemExit(proc.returncode)
    except FileNotFoundError:
        click.echo("请先安装 UI 依赖: pip install mix-tools[ui]", err=True)
        raise SystemExit(1)


@main.group("data")
def data_group() -> None:
    """数据处理：JSON/CSV 转换、去重、对比、SQL 生成"""
    pass


@data_group.command("json2csv")
@click.argument("json_file", type=click.Path(exists=True))
@click.argument("csv_file", type=click.Path())
def cmd_json2csv(json_file: str, csv_file: str) -> None:
    """JSON 数组转 CSV"""
    n = _json_to_csv(json_file, csv_file)
    click.echo(f"已转换 {n} 条记录 -> {csv_file}")


@data_group.command("csv2json")
@click.argument("csv_file", type=click.Path(exists=True))
@click.argument("json_file", type=click.Path())
def cmd_csv2json(csv_file: str, json_file: str) -> None:
    """CSV 转 JSON 数组"""
    n = _csv_to_json(csv_file, json_file)
    click.echo(f"已转换 {n} 条记录 -> {json_file}")


@data_group.command("dedup")
@click.argument("input_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
@click.option("-s", "--separator", default=",", help="输出分隔符")
def cmd_dedup(input_file: str, output_file: str, separator: str) -> None:
    """文件按行去重，输出为分隔符连接的单行"""
    orig, uniq = _dedup_file(input_file, output_file, separator=separator)
    click.echo(f"{input_file}: {orig} -> {uniq} 行，输出 {output_file}")


@data_group.command("compare")
@click.argument("file_a", type=click.Path(exists=True))
@click.argument("file_b", type=click.Path(exists=True))
@click.option("-s", "--separator", default=",", help="单行多列时的分隔符")
@click.option("-o", "--output", type=click.Path(), help="将共同项写入文件")
def cmd_compare(file_a: str, file_b: str, separator: str, output: str | None) -> None:
    """对比两文件中的项，输出仅在 A、仅在 B、共同的项"""
    only_a, only_b, common = _compare_files(file_a, file_b, sep=separator)
    click.echo(f"仅在 A: {len(only_a)}, 仅在 B: {len(only_b)}, 共同: {len(common)}")
    if common and output:
        sorted_common = _sort_items_numeric(common)
        Path(output).write_text(",".join(sorted_common), encoding="utf-8")
        click.echo(f"共同项已写入 {output}")


@data_group.command("gen-sql")
@click.argument("input_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
@click.option("-r", "--remark", default="", help="备注列默认值")
@click.option("-t", "--table", default="hibox_orders.device_need_sync_order", help="表名")
def cmd_gen_sql(input_file: str, output_file: str, remark: str, table: str) -> None:
    """根据文件每行一个编码，生成批量 INSERT SQL"""
    n = _generate_insert_sql(input_file, output_file, table=table, remark=remark)
    click.echo(f"已生成 {n} 条 INSERT -> {output_file}")


@data_group.command("find-dup")
@click.argument("json_file", type=click.Path(exists=True))
@click.option("-k", "--key", default="原编码", help="去重键列名")
def cmd_find_dup(json_file: str, key: str) -> None:
    """在 JSON 中按键查找重复项"""
    dup = _find_dup_json(json_file, key_column=key)
    click.echo(f"发现 {len(dup)} 个重复键")
    for k, recs in list(dup.items())[:5]:
        click.echo(f"  {k}: {len(recs)} 条")


@data_group.command("filter-json")
@click.argument("json_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
@click.option("-k", "--key", default="原编码", help="去重键")
@click.option("-c", "--columns", multiple=True, help="保留的列")
def cmd_filter_json(json_file: str, output_file: str, key: str, columns: tuple[str, ...]) -> None:
    """JSON 按键去重并输出"""
    cols = list(columns) if columns else None
    n = _filter_json_dedup(json_file, output_file, key_columns=[key], keep_columns=cols)
    click.echo(f"去重后 {n} 条 -> {output_file}")


@data_group.command("check-csv-dup")
@click.argument("csv_file", type=click.Path(exists=True))
@click.option("-k", "--key", default="原编码", help="键列")
def cmd_check_csv_dup(csv_file: str, key: str) -> None:
    """检查 CSV 中是否存在重复键"""
    ok, total, unique = _check_csv_dup(csv_file, key_column=key)
    click.echo(f"总行: {total}, 唯一键: {unique}, 无重复: {ok}")


@data_group.command("verify-csv")
@click.argument("json_file", type=click.Path(exists=True))
@click.argument("csv_file", type=click.Path(exists=True))
@click.option("-o", "--errors-output", type=click.Path(), help="错误详情输出 CSV")
def cmd_verify_csv(json_file: str, csv_file: str, errors_output: str | None) -> None:
    """以 JSON 为基准校验 CSV 映射是否正确"""
    correct, err_count, errors = _verify_csv_json(json_file, csv_file)
    click.echo(f"正确: {correct}, 错误: {err_count}")
    if errors and errors_output:
        import pandas as pd
        pd.DataFrame(errors).to_csv(errors_output, index=False, encoding="utf-8-sig")
        click.echo(f"错误详情 -> {errors_output}")


@main.group("excel")
def excel_group() -> None:
    """Excel 处理"""
    pass


@excel_group.command("to-json")
@click.argument("excel_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
@click.option("-s", "--sheet", default="0", help="Sheet 名或索引")
def cmd_excel_to_json(excel_file: str, output_file: str, sheet: str) -> None:
    """Excel 指定 Sheet 转 JSON"""
    sheet_val: str | int = int(sheet) if sheet.isdigit() else sheet
    n = _excel_to_json(excel_file, output_file, sheet_name=sheet_val)
    click.echo(f"已转换 {n} 条 -> {output_file}")


@excel_group.command("device-mapping")
@click.argument("device_list", type=click.Path(exists=True))
@click.argument("excel_file", type=click.Path(exists=True))
@click.argument("output_csv", type=click.Path())
@click.option("-s", "--sheet", default="0", help="Sheet 名或索引")
def cmd_device_mapping(
    device_list: str,
    excel_file: str,
    output_csv: str,
    sheet: str,
) -> None:
    """根据设备清单和 Excel 生成 原编码/换码/最终编码 CSV"""
    sheet_val: str | int = int(sheet) if sheet.isdigit() else sheet
    n = _gen_device_csv(device_list, excel_file, sheet_val, output_csv)
    click.echo(f"已生成 {n} 条 -> {output_csv}")
