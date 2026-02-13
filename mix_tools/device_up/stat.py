# -*- coding: utf-8 -*-
"""
设备同步统计：解析订单 JSON，按设备码统计订单数、NFC 订单数及订单号
支持 .json 或 .json.gz 压缩包
"""

import json
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from mix_tools.device_up.utils import open_json_or_gz


@dataclass
class DeviceUpStat:
    """设备统计信息"""

    device_code: str
    nfc_order_count: int = 0
    order_count: int = 0
    nfc_order_codes: list[str] = field(default_factory=list)

    def to_row(self) -> dict:
        """转为 Excel 行数据"""
        codes_str = ",".join(self.nfc_order_codes) if self.nfc_order_codes else ""
        return {
            "设备编码": self.device_code,
            "NFC订单数": self.nfc_order_count,
            "订单数": self.order_count,
            "NFC订单号": codes_str,
        }


def _parse_order_line(line: str) -> dict | None:
    """
    解析单行 JSON，提取 request body 中的 data 部分。
    期望格式：content 中包含 "request body: {...},request seq:"
    """
    try:
        obj = json.loads(line)
        content = obj.get("content")
        if not content or not isinstance(content, str):
            return None
        prefix = "request url: https://upop.pec.com.cn/wheat/order,request body:"
        suffix = ",request seq:"
        if prefix not in content or suffix not in content:
            return None
        start = content.index(prefix) + len(prefix)
        end = content.index(suffix, start)
        body_str = content[start:end]
        req = json.loads(body_str)
        return req.get("data")
    except Exception:
        return None


def up_sync_device_stat(
    json_file: str | Path,
    output_excel: str | Path,
    device_file: str | Path | None = None,
) -> tuple[int, int]:
    """
    设备同步统计：读取订单 JSON，输出 Excel。
    可选设备列表：若有则输出「按设备列表」+「全部统计」两 sheet，否则仅输出「全部统计」。

    :param json_file: 订单 JSON 文件（或 .json.gz 压缩包），每行一条 JSON 记录
    :param output_excel: 输出 Excel 路径
    :param device_file: 可选，设备码列表文件（每行一个），用于「按设备列表」sheet
    :return: (设备列表数量, 有订单的设备数)
    """
    path_json = Path(json_file)
    path_out = Path(output_excel)

    device_codes: list[str] = []
    if device_file is not None:
        path_device = Path(device_file)
        seen: set[str] = set()
        with path_device.open(encoding="utf-8") as f:
            for line in f:
                code = line.strip()
                if code and code not in seen:
                    seen.add(code)
                    device_codes.append(code)

    device_stat_map: dict[str, DeviceUpStat] = {}

    with open_json_or_gz(path_json) as f:
        for line in f:
            data = _parse_order_line(line)
            if not data:
                continue
            device_sn = data.get("deviceSn")
            if not device_sn:
                continue
            stat = device_stat_map.get(device_sn)
            if stat:
                stat.order_count += 1
            else:
                stat = DeviceUpStat(device_code=device_sn, order_count=1)
                device_stat_map[device_sn] = stat

            pay_type = data.get("payType", "")
            if str(pay_type).lower() == "nfc":
                stat.nfc_order_count += 1
                order_no = data.get("orderNo", "")
                payee_type = data.get("payee_type", "")
                stat.nfc_order_codes.append(f"{order_no}({payee_type})")

    path_out.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path_out, engine="openpyxl") as writer:
        if device_codes:
            rows_by_device = []
            for code in device_codes:
                stat = device_stat_map.get(code.strip())
                if stat is None:
                    stat = DeviceUpStat(device_code=code.strip(), nfc_order_count=0, order_count=0)
                rows_by_device.append(stat.to_row())
            pd.DataFrame(rows_by_device).to_excel(writer, sheet_name="按设备列表", index=False)
        rows_all = [s.to_row() for s in device_stat_map.values()]
        pd.DataFrame(rows_all).to_excel(writer, sheet_name="全部统计", index=False)

    return len(device_codes), len(device_stat_map)
