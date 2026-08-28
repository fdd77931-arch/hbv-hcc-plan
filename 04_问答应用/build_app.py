# -*- coding: utf-8 -*-
"""
构建脚本：主表 CSV → 问答应用 index.html（内嵌 JSON 数据）
用法：python3 build_app.py [主表CSV路径]
输出：../03_问答应用/index.html
后续主表更新后重跑本脚本即可刷新问答应用数据。
"""
import csv
import io
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
MASTER_CSV = os.path.join(BASE, "..", "01_主表", "样例卡片_10条.csv")
if len(sys.argv) > 1:
    MASTER_CSV = sys.argv[1]
TEMPLATE = os.path.join(BASE, "index.template.html")
OUTPUT = os.path.join(BASE, "index.html")

# 构建时可精简的字段（保留核心字段，控制 JSON 体积）
KEEP_KEYS = [
    "文献唯一标识", "PMID", "DOI", "中文标题", "发布年份", "发布日期",
    "期刊或发布机构", "第一作者", "通讯作者", "作者单位", "国家/地区",
    "是否中国研究", "是否中国多中心研究", "文献类型", "证据等级", "研究设计",
    "研究阶段", "样本量", "研究人群", "初治/经治", "HBeAg状态", "是否肝硬化",
    "治疗方案", "对照方案", "治疗时间", "随访时间", "基线HBsAg", "基线HBV DNA",
    "HBsAg下降速度或变化幅度", "HBV DNA下降速度或变化幅度", "主要终点",
    "HBsAg清除率", "HBeAg血清学转换率", "病毒学应答率", "生化学应答率",
    "肝癌发生或复发结局", "安全性", "核心结论", "临床价值",
    "对中国实践的启示", "对2030行动的意义", "对全国肝病联盟的意义",
    "所属筛诊治管康环节", "所属一级专题", "所属二级专题", "适用患者分层",
    "当前争议", "研究局限", "是否建议重点阅读", "建议关注优先级",
    "原文链接", "二次解读链接",
]

def short_key(full_key):
    """去掉 '[组名] ' 前缀，保留字段短名"""
    if "] " in full_key:
        return full_key.split("] ", 1)[1]
    return full_key

def main():
    if not os.path.exists(MASTER_CSV):
        print("错误：找不到主表文件", MASTER_CSV)
        sys.exit(1)

    rows = list(csv.DictReader(io.open(MASTER_CSV, encoding="utf-8-sig")))
    if not rows:
        print("错误：主表为空")
        sys.exit(1)

    # 表头规范化：去组名前缀
    raw_headers = list(rows[0].keys())
    header_map = {h: short_key(h) for h in raw_headers}

    cards = []
    for r in rows:
        card = {}
        for h in raw_headers:
            sk = header_map[h]
            if sk in KEEP_KEYS:
                v = (r[h] or "").strip()
                card[sk] = v
        cards.append(card)

    data = {
        "meta": {
            "name": "全国肝病联盟与2030慢性肝病行动专题知识库",
            "version": "0.1",
            "updated": "2026-08-28",
            "card_count": len(cards),
            "field_count": len(KEEP_KEYS),
        },
        "cards": cards,
    }

    json_str = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    with io.open(TEMPLATE, encoding="utf-8") as f:
        html = f.read()

    html = html.replace("__KB_DATA__", json_str)

    with io.open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)

    # 统计
    topics = {}
    levels = {"A": 0, "B": 0, "C": 0, "D": 0}
    china = 0
    for c in cards:
        t = c.get("所属一级专题", "?") or "?"
        topics[t] = topics.get(t, 0) + 1
        lv = c.get("证据等级", "D")
        if lv in levels:
            levels[lv] += 1
        if c.get("是否中国研究") in ("是", "中国", "中国研究"):
            china += 1

    print("构建成功 →", OUTPUT)
    print("卡片数:", len(cards))
    print("专题分布:", topics)
    print("证据等级: A={} B={} C={} D={}".format(levels["A"], levels["B"], levels["C"], levels["D"]))
    print("中国研究:", china)
    print("JSON 体积: {:.1f} KB".format(len(json_str.encode("utf-8")) / 1024))

if __name__ == "__main__":
    main()
