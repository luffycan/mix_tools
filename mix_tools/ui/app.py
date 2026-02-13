# -*- coding: utf-8 -*-
"""
Mix Tools 可视化界面 - Streamlit Web UI
"""

import tempfile
from pathlib import Path

import streamlit as st

from mix_tools.data.dedup import dedup_file
from mix_tools.data.duplicates import check_csv_duplicates, find_duplicates_in_json, filter_json_dedup
from mix_tools.data.file_compare import compare_files, sort_items_numeric
from mix_tools.data.json_csv import csv_to_json, json_to_csv
from mix_tools.data.sql_generate import generate_insert_sql
from mix_tools.data.verify import verify_csv_against_json
from mix_tools.excel.convert import excel_to_json, generate_device_mapping_csv
from mix_tools.device_up.stat import up_sync_device_stat
from mix_tools.device_up.up_orders import check_device_orders

st.set_page_config(
    page_title="Mix Tools",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 侧边栏导航
st.sidebar.title("Mix Tools")
st.sidebar.markdown("文档 / Excel / 数据处理小工具")

page = st.sidebar.radio(
    "选择功能",
    [
        "📄 JSON↔CSV 转换",
        "📋 文本去重",
        "🔀 文件对比",
        "📝 生成 SQL",
        "🔍 重复检测",
        "✅ CSV 校验",
        "📊 Excel 转换",
        "📱 设备统计",
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption("启动后手动打开: http://localhost:8501")

# ========== JSON↔CSV ==========
if page == "📄 JSON↔CSV 转换":
    st.header("JSON 与 CSV 互转")
    sub = st.radio("转换方向", ["JSON → CSV", "CSV → JSON"], horizontal=True)

    if sub == "JSON → CSV":
        col1, col2 = st.columns(2)
        with col1:
            json_file = st.file_uploader("选择 JSON 文件", type=["json"])
        with col2:
            csv_name = st.text_input("输出 CSV 文件名", value="output.csv")
        if json_file and csv_name:
            if st.button("转换"):
                with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
                    tf.write(json_file.getvalue())
                    path = tf.name
                try:
                    out_path = tempfile.mktemp(suffix=".csv")
                    n = json_to_csv(path, out_path)
                    data = Path(out_path).read_bytes()
                    st.download_button("下载 CSV", data=data, file_name=csv_name, mime="text/csv")
                    st.success(f"已转换 {n} 条记录")
                except Exception as e:
                    st.error(str(e))
    else:
        col1, col2 = st.columns(2)
        with col1:
            csv_file = st.file_uploader("选择 CSV 文件", type=["csv"])
        with col2:
            json_name = st.text_input("输出 JSON 文件名", value="output.json")
        if csv_file and json_name:
            if st.button("转换"):
                with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
                    tf.write(csv_file.getvalue())
                    path = tf.name
                try:
                    out_path = tempfile.mktemp(suffix=".json")
                    n = csv_to_json(path, out_path)
                    data = Path(out_path).read_bytes()
                    st.download_button("下载 JSON", data=data, file_name=json_name, mime="application/json")
                    st.success(f"已转换 {n} 条记录")
                except Exception as e:
                    st.error(str(e))

# ========== 文本去重 ==========
elif page == "📋 文本去重":
    st.header("文本去重")
    uploaded = st.file_uploader("上传文本文件（每行一项）", type=["txt"])
    sep = st.text_input("输出分隔符", value=",", help="空表示每行一个")
    if uploaded:
        if st.button("去重"):
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
                tf.write(uploaded.getvalue())
                path = tf.name
            out_path = tempfile.mktemp(suffix=".txt")
            try:
                orig, uniq = dedup_file(path, out_path, separator=sep)
                data = Path(out_path).read_bytes()
                st.download_button("下载结果", data=data, file_name="dedup_output.txt", mime="text/plain")
                st.success(f"原始 {orig} 行 → 去重后 {uniq} 行")
            except Exception as e:
                st.error(str(e))

# ========== 文件对比 ==========
elif page == "🔀 文件对比":
    st.header("文件对比")
    col1, col2 = st.columns(2)
    with col1:
        file_a = st.file_uploader("文件 A", type=["txt", "csv"])
    with col2:
        file_b = st.file_uploader("文件 B", type=["txt", "csv"])
    sep = st.text_input("分隔符（单行多列时）", value=",")

    if file_a and file_b:
        if st.button("对比"):
            with tempfile.NamedTemporaryFile(suffix=Path(file_a.name).suffix, delete=False) as t1:
                t1.write(file_a.getvalue())
                pa = t1.name
            with tempfile.NamedTemporaryFile(suffix=Path(file_b.name).suffix, delete=False) as t2:
                t2.write(file_b.getvalue())
                pb = t2.name
            try:
                only_a, only_b, common = compare_files(pa, pb, sep=sep or None)
                st.metric("仅在 A", len(only_a))
                st.metric("仅在 B", len(only_b))
                st.metric("共同", len(common))
                if common:
                    sorted_common = sort_items_numeric(common)
                    st.text_area("共同项（逗号分隔）", ",".join(sorted_common), height=200)
            except Exception as e:
                st.error(str(e))

# ========== 生成 SQL ==========
elif page == "📝 生成 SQL":
    st.header("生成批量统一订单插入语句 INSERT SQL")
    uploaded = st.file_uploader("上传编码列表（每行一个）", type=["txt"])
    remark = st.text_input("备注列默认值", value="")
    table = st.text_input("表名", value="hibox_orders.device_need_sync_order")
    if uploaded:
        if st.button("生成"):
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
                tf.write(uploaded.getvalue())
                path = tf.name
            out_path = tempfile.mktemp(suffix=".sql")
            try:
                n = generate_insert_sql(path, out_path, table=table, remark=remark)
                data = Path(out_path).read_bytes()
                st.download_button("下载 SQL", data=data, file_name="insert.sql", mime="text/plain")
                st.success(f"已生成 {n} 条 INSERT")
            except Exception as e:
                st.error(str(e))

# ========== 重复检测 ==========
elif page == "🔍 重复检测":
    st.header("重复检测")
    sub = st.radio("检测类型", ["JSON 按键重复", "JSON 去重输出", "CSV 重复检查"], horizontal=True)

    if sub == "JSON 按键重复":
        uploaded = st.file_uploader("上传 JSON", type=["json"])
        key = st.text_input("键列名", value="原编码")
        if uploaded:
            if st.button("检测"):
                with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
                    tf.write(uploaded.getvalue())
                    path = tf.name
                try:
                    dup = find_duplicates_in_json(path, key_column=key)
                    st.write(f"发现 {len(dup)} 个重复键")
                    for k, recs in list(dup.items())[:20]:
                        st.expander(f"{k} ({len(recs)} 条)").write(recs)
                except Exception as e:
                    st.error(str(e))

    elif sub == "JSON 去重输出":
        uploaded = st.file_uploader("上传 JSON", type=["json"])
        key = st.text_input("键列名", value="原编码")
        if uploaded:
            if st.button("去重并下载"):
                with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
                    tf.write(uploaded.getvalue())
                    path = tf.name
                out_path = tempfile.mktemp(suffix=".json")
                try:
                    n = filter_json_dedup(path, out_path, key_columns=[key])
                    data = Path(out_path).read_bytes()
                    st.download_button("下载", data=data, file_name="filtered.json", mime="application/json")
                    st.success(f"去重后 {n} 条")
                except Exception as e:
                    st.error(str(e))

    else:
        uploaded = st.file_uploader("上传 CSV", type=["csv"])
        key = st.text_input("键列名", value="原编码")
        if uploaded:
            if st.button("检查"):
                with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tf:
                    tf.write(uploaded.getvalue())
                    path = tf.name
                try:
                    ok, total, unique = check_csv_duplicates(path, key_column=key)
                    st.metric("总行数", total)
                    st.metric("唯一键数", unique)
                    st.success("无重复") if ok else st.warning("存在重复")
                except Exception as e:
                    st.error(str(e))

# ========== CSV 校验 ==========
elif page == "✅ CSV 校验":
    st.header("以 JSON 为基准校验 CSV")
    col1, col2 = st.columns(2)
    with col1:
        json_file = st.file_uploader("基准 JSON", type=["json"])
    with col2:
        csv_file = st.file_uploader("待校验 CSV", type=["csv"])
    if json_file and csv_file:
        if st.button("校验"):
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tj:
                tj.write(json_file.getvalue())
                pj = tj.name
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tc:
                tc.write(csv_file.getvalue())
                pc = tc.name
            try:
                correct, err_count, errors = verify_csv_against_json(pj, pc)
                st.metric("正确", correct)
                st.metric("错误", err_count)
                if errors:
                    import pandas as pd
                    st.dataframe(pd.DataFrame(errors), use_container_width=True)
            except Exception as e:
                st.error(str(e))

# ========== Excel 转换 ==========
elif page == "📊 Excel 转换":
    st.header("Excel 转换")
    sub = st.radio("功能", ["Excel → JSON", "设备映射 CSV"], horizontal=True)

    if sub == "Excel → JSON":
        excel_file = st.file_uploader("上传 Excel", type=["xlsx", "xls"])
        sheet = st.text_input("Sheet 名或索引", value="0")
        if excel_file:
            if st.button("转换"):
                with tempfile.NamedTemporaryFile(suffix=Path(excel_file.name).suffix, delete=False) as tf:
                    tf.write(excel_file.getvalue())
                    path = tf.name
                out_path = "output.json"
                try:
                    out_path = tempfile.mktemp(suffix=".json")
                    sheet_val = int(sheet) if sheet.isdigit() else sheet
                    n = excel_to_json(path, out_path, sheet_name=sheet_val)
                    data = Path(out_path).read_bytes()
                    st.download_button("下载 JSON", data=data, file_name="output.json", mime="application/json")
                    st.success(f"已转换 {n} 条")
                except Exception as e:
                    st.error(str(e))
    else:
        device_file = st.file_uploader("设备清单（每行一个编码）", type=["txt"])
        excel_file = st.file_uploader("Excel 映射表", type=["xlsx", "xls"])
        sheet = st.text_input("Sheet 名或索引", value="0")
        if device_file and excel_file:
            if st.button("生成"):
                with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as td:
                    td.write(device_file.getvalue())
                    path_device = td.name
                with tempfile.NamedTemporaryFile(suffix=Path(excel_file.name).suffix, delete=False) as te:
                    te.write(excel_file.getvalue())
                    path_excel = te.name
                out_path = "device_mapping.csv"
                try:
                    out_path = tempfile.mktemp(suffix=".csv")
                    sheet_val = int(sheet) if sheet.isdigit() else sheet
                    n = generate_device_mapping_csv(path_device, path_excel, sheet_val, out_path)
                    data = Path(out_path).read_bytes()
                    st.download_button("下载 CSV", data=data, file_name="device_mapping.csv", mime="text/csv")
                    st.success(f"已生成 {n} 条")
                except Exception as e:
                    st.error(str(e))

# ========== 设备统计 ==========
elif page == "📱 设备统计":
    st.header("设备订单统计")
    sub = st.radio("功能", ["设备同步统计", "设备订单校验"], horizontal=True)

    if sub == "设备同步统计":
        json_file = st.file_uploader("订单 JSON 或 .json.gz 压缩包（每行一条）", type=["json", "gz"])
        device_file = st.file_uploader("设备列表（可选，每行一个编码）", type=["txt"], help="不传则仅输出 JSON 中出现的设备统计")
        if json_file:
            if st.button("统计"):
                suffix = Path(json_file.name).suffix
                with tempfile.NamedTemporaryFile(suffix=suffix if suffix == ".gz" else ".json", delete=False) as tj:
                    tj.write(json_file.getvalue())
                    path_json = tj.name
                path_device = None
                if device_file:
                    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as td:
                        td.write(device_file.getvalue())
                        path_device = td.name
                out_excel = tempfile.mktemp(suffix=".xlsx")
                try:
                    n_dev, n_has = up_sync_device_stat(path_json, out_excel, path_device)
                    st.success(f"有订单设备 {n_has} 个" + (f"，设备列表 {n_dev} 个" if n_dev else ""))
                    data_excel = Path(out_excel).read_bytes()
                    st.download_button("下载 Excel", data=data_excel, file_name="device_up_stat.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                except Exception as e:
                    st.error(str(e))

    else:
        device_file = st.file_uploader("设备列表（每行一个编码）", type=["txt"])
        json_file = st.file_uploader("订单 JSON 或 .json.gz 压缩包（每行一条）", type=["json", "gz"])
        if device_file and json_file:
            if st.button("校验"):
                with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as td:
                    td.write(device_file.getvalue())
                    path_device = td.name
                suffix = Path(json_file.name).suffix
                with tempfile.NamedTemporaryFile(suffix=suffix if suffix == ".gz" else ".json", delete=False) as tj:
                    tj.write(json_file.getvalue())
                    path_json = tj.name
                try:
                    all_set, nfc_set, no_order = check_device_orders(path_device, path_json)
                    st.metric("JSON 中设备数", len(all_set))
                    st.metric("NFC 设备数", len(nfc_set))
                    st.metric("无订单设备数", len(no_order))
                    if no_order:
                        st.text_area("无订单设备", "\n".join(sorted(no_order)), height=200)
                except Exception as e:
                    st.error(str(e))

def _is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


if __name__ == "__main__":
    import subprocess
    import sys

    DEFAULT_PORT = 8501
    if _is_port_in_use(DEFAULT_PORT):
        print(f"Mix Tools UI 已在运行，请访问 http://localhost:{DEFAULT_PORT}")
        print("如需重启，请先关闭已有进程。")
        sys.exit(0)

    args = [
        sys.executable, "-m", "streamlit", "run", __file__,
        "--server.port", str(DEFAULT_PORT),
        "--server.headless", "true",
        "--server.portRetries", "0",
        *sys.argv[1:],
    ]
    sys.exit(subprocess.run(args, check=False).returncode)
