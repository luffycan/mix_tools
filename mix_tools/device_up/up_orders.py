# -*- coding: utf-8 -*-
"""
订单设备校验：从 JSON 中提取出现过的设备码，与设备列表对比
支持 .json 或 .json.gz 压缩包
"""

import json
from pathlib import Path

from mix_tools.device_up.utils import open_json_or_gz


def _parse_data_from_line(line: str) -> tuple[str | None, bool]:
    """
    解析单行 JSON，提取 request body data 中的 deviceSn 和 payType。
    期望 content 包含 "request body: {...},request seq:"
    :return: (deviceSn, is_nfc)
    """
    try:
        obj = json.loads(line)
        content = obj.get("content")
        if not content or not isinstance(content, str):
            return None, False
        prefix = "request url: https://upop.pec.com.cn/wheat/order,request body:"
        suffix = ",request seq:"
        if prefix not in content or suffix not in content:
            return None, False
        start = content.index(prefix) + len(prefix)
        end = content.index(suffix, start)
        body_str = content[start:end]
        req = json.loads(body_str)
        data = req.get("data")
        if not data:
            return None, False
        device_sn = data.get("deviceSn")
        is_nfc = str(data.get("payType", "")).lower() == "nfc"
        return device_sn, is_nfc
    except Exception:
        return None, False


def check_device_orders(
    device_list: str | Path,
    json_file: str | Path,
) -> tuple[set[str], set[str], set[str]]:
    """
    校验设备订单：统计 JSON 中出现过的设备、NFC 设备，以及与设备列表的差集。

    :param device_list: 设备码列表文件或字符串（换行分隔）
    :param json_file: 订单 JSON 文件（或 .json.gz 压缩包），每行一条
    :return: (all_set, nfc_set, device_list中有但 JSON 中无订单的设备)
    """
    if isinstance(device_list, (str, Path)):
        path = Path(device_list)
        if path.exists():
            device_set = {ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()}
        else:
            device_set = {ln.strip() for ln in str(device_list).splitlines() if ln.strip()}
    else:
        device_set = set()

    all_set: set[str] = set()
    nfc_set: set[str] = set()
    path_json = Path(json_file)

    with open_json_or_gz(path_json) as f:
        for line in f:
            device_sn, is_nfc = _parse_data_from_line(line)
            if not device_sn:
                continue
            all_set.add(device_sn)
            if is_nfc:
                nfc_set.add(device_sn)

    no_order_set = device_set - all_set
    return all_set, nfc_set, no_order_set
