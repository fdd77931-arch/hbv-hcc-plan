# -*- coding: utf-8 -*-
"""S2 溯源核实：候选线索归并去重
把多个公众号转发同一文献的条目归并为一条唯一文献实体，
减少逐条溯源工作量，输出唯一文献清单。
用法：python3 归并去重.py [T1_指南政策 T2_筛查 ...]
"""
import csv, io, re, sys, os
from collections import defaultdict, OrderedDict

BASE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE, "..", "S1_候选线索池", "优选候选池_500篇.csv")

# ---------- 标题清洗 ----------
STRIP_PREFIX = [
    "「转」", "【转】", "[转]", "转发", "转载",
    "权威发布", "重磅发布", "重磅首发", "全文首发", "正式发布", "正式版",
    "指南与共识", "指南共识", "指南发布", "最新发布", "定稿版首发",
    "首版发布", "全文发布", "指南全文", "指南下载", "抢先看", "抢先看！",
    "精华版", "速览", "推荐意见抢先看", "18条推荐意见抢先看",
    "会议撷萃", "会议回放", "学术争鸣", "专家论坛", "述评", "远程教育",
    "期刊导读", "聚焦两会", "荣誉时刻", "喜报", "邀您加入", "问卷调研",
    "学术争鸣 ｜", "会议撷萃 ｜", "聚焦两会 ｜",
]
STRIP_SUFFIX = [
    "抢先看", "重磅发布！", "正式发表", "发布！", "重磅来袭",
]

def clean_title(t):
    """清洗标题：去掉转发标记/前缀/公众号名，提取文献实体关键词"""
    t = t.strip()
    # 去掉「转」类标记
    t = re.sub(r"^[「【\[]?\s*转\s*[」】\]]?\s*", "", t)
    t = re.sub(r"^「转」", "", t)
    # 去掉 "xxx ｜ 内容" 中的公众号前缀（｜前通常为栏目/号名）
    # 保留 ｜ 后内容，若 ｜ 前含"指南/共识/解读"等关键词则保留整个
    if "｜" in t or "|" in t:
        sep = "｜" if "｜" in t else "|"
        parts = [p.strip() for p in t.split(sep)]
        # 选含 指南/共识/解读/建议/规范/行动/计划/报告 最长的段
        key_parts = [p for p in parts if re.search(r"指南|共识|解读|建议|规范|行动|计划|肝炎|乙肝|筛查|疫苗|消除|管理", p)]
        if key_parts:
            t = max(key_parts, key=len)
        else:
            t = max(parts, key=len)
    for p in STRIP_PREFIX:
        if t.startswith(p):
            t = t[len(p):]
    for s in STRIP_SUFFIX:
        if t.endswith(s):
            t = t[: -len(s)]
    t = re.sub(r"\s+", "", t)
    return t.strip(" ｜|，。！!；;、")

# ---------- 文献实体关键词（用于归并） ----------
# 每个实体：核心标题关键词 → 规范名称
ENTITIES = [
    # T1 指南/共识/政策
    (r"慢性乙型肝炎防治指南.*2022|2022.*慢性乙型肝炎防治指南", "慢性乙型肝炎防治指南(2022年版)"),
    (r"慢性乙型肝炎防治指南.*2019|2019.*慢性乙型肝炎防治指南", "慢性乙型肝炎防治指南(2019年版)"),
    (r"儿童慢性乙型肝炎防治专家共识", "儿童慢性乙型肝炎防治专家共识(2024)"),
    (r"乙型肝炎病毒母婴传播防治指南", "乙型肝炎病毒母婴传播防治指南(2024年版)"),
    (r"成人乙型肝炎疫苗接种专家建议", "成人乙型肝炎疫苗接种专家建议(2024)"),
    (r"成人乙型肝炎病毒感染筛查、检测及管理专家建议", "成人乙型肝炎病毒感染筛查检测及管理专家建议(2024)"),
    (r"乙型肝炎病毒标志物临床应用专家共识", "乙型肝炎病毒标志物临床应用专家共识(2023)"),
    (r"肝纤维化MRI诊断专家共识", "慢性乙型肝炎肝纤维化MRI诊断专家共识(2023年版)"),
    (r"乙型病毒性肝炎全人群管理专家共识", "乙型病毒性肝炎全人群管理专家共识(2023)"),
    (r"戊型病毒性肝炎院内筛查管理流程专家共识", "戊型病毒性肝炎院内筛查管理流程专家共识(2023年版)"),
    (r"乙型病毒性肝炎相关肝细胞癌围手术期抗病毒治疗规范", "乙型病毒性肝炎相关HCC围手术期抗病毒治疗规范"),
    (r"聚乙二醇干扰素α治疗慢性乙型肝炎专家共识|Peg-IFN.*共识", "聚乙二醇干扰素α治疗慢性乙型肝炎专家共识"),
    (r"干扰素α治疗不良反应临床处理专家共识", "慢性病毒性肝炎干扰素α不良反应临床处理专家共识"),
    (r"WHO.*2024.*指南|世界卫生组织2024年版乙型肝炎防治指南", "WHO 2024年版乙型肝炎防治指南(中国比较解读)"),
    (r"WHO 2022-2030消除病毒性肝炎行动计划|2022-2030.*行动计划", "WHO 2022-2030消除病毒性肝炎行动计划(解读)"),
    (r"消除病毒性肝炎.*倡议|大湾区.*倡议", "大湾区消除病毒性肝炎倡议"),
    (r"乙肝临床治愈门诊|209家医院", "全国209家医院乙肝临床治愈门诊建设"),
    (r"海南省消除病毒性肝炎", "海南省消除病毒性肝炎实践"),
    (r"建立公共卫生管理模式", "建立公共卫生管理模式促进消除肝炎危害(王宇述评)"),
    (r"全球消除病毒性肝炎的公共卫生威胁", "全球消除病毒性肝炎公共卫生威胁(崔富强)"),
    (r"中国建国以来防控病毒性肝炎", "中国建国以来防控病毒性肝炎工作进展(崔富强庄辉)"),
    (r"中国病毒性肝炎疾病负担研究进展", "中国病毒性肝炎疾病负担研究进展"),
    (r"2004-2016.*报告发病率|报告发病率变化", "2004-2016中国病毒性肝炎报告发病率研究"),
    (r"2006—2021.*死亡|乙型肝炎相关死亡", "2006-2021中国居民乙肝相关死亡流行特征"),
    (r"孕产妇乙型肝炎病毒现症感染", "2021-2023中国孕产妇乙肝现症感染流行病学"),
    (r"妊娠期病毒性肝炎的管理", "妊娠期病毒性肝炎管理指南推荐"),
    (r"迈向再无病毒性肝炎威胁", "迈向再无病毒性肝炎威胁的2030(吴晓宁等)"),
    (r"中国式乙型肝炎.*全治|全治", "积极推进中国式乙型肝炎全治(建议)"),
    (r"关于2022年版慢性乙型肝炎防治指南4个问题", "庄辉院士:2022版指南4个问题讨论"),
    (r"修订要点商榷|修订过程中关于慢性HBV感染自然史", "2022版指南修订要点讨论"),
    (r"2019年版.*治疗部分解读|王贵强.*2019|王贵强", "2019版指南治疗部分解读(王贵强)"),
    (r"贾继东.*十大更新|十大更新要点", "2022版指南十大更新要点(贾继东)"),
    (r"更新要点解读|解读.*2022年版|2022年版.*解读", "2022版指南更新要点解读"),
    (r"HBeAg阴性慢性HBV感染者HBV DNA阴性是否合适", "2022版指南学术争鸣(HBeAg阴性HBV DNA)"),
    (r"自然史分期及其内涵", "2022版指南学术争鸣(自然史分期)"),
    (r"对《慢性乙型肝炎防治指南（2022年版）》的商榷|商榷", "2022版指南学术争鸣(商榷)"),
    (r"从.*Treat All.*时代迈进|Treat All", "从2022版指南向Treat All时代迈进(窦晓光)"),
    (r"2024大湾区肝病国际论坛|大湾区肝病国际论坛|消除病毒性肝炎大会", "大湾区肝病国际论坛暨消除病毒性肝炎大会"),
    (r"消除肝炎.*积极行动|世界肝炎日", "世界肝炎日行动(2024)"),
    (r"SunShine|病毒性肝炎防治指南实践工程", "病毒性肝炎防治指南实践工程SunShine项目"),
    (r"主动筛查，精准检测|主动筛查 精准检测", "主动筛查精准检测消除肝炎行动"),
    (r"中国消除病毒性肝炎公共卫生危害的进展", "中国消除病毒性肝炎公共卫生危害进展"),
    (r"消除病毒性肝炎，应从.*顶层设计|顶层设计", "消除病毒性肝炎从顶层设计开始(任红)"),
    (r"血清乙型肝炎病毒前基因组RNA", "血清HBV前基因组RNA变化特点研究"),
    (r"抗病毒治疗方案类型横断面调查", "慢乙肝抗病毒治疗方案类型横断面调查"),
    (r"基于Andersen模型", "基于Andersen模型丙肝治疗相关因素(徐朋等)"),
    (r"不同类型抗病毒治疗适应证临床病理特征", "慢乙肝不同类型抗病毒治疗适应证病理特征(胡爱荣)"),
    (r"丙型肝炎微消除|福星计划", "珠海丙肝微消除福星计划结果"),
    (r"消除丙型肝炎公共卫生危害行动", "中国消除丙肝公共卫生危害行动进展"),
    (r"儿童病毒性肝炎的诊治进展", "儿童病毒性肝炎诊治进展(许红梅)"),
    (r"2004-2016", "2004-2016中国病毒性肝炎报告发病率研究"),
    # T2 筛查
    (r"乙肝表面抗原阳性成人肝癌筛查与监测管理培训|星光项目", "HBsAg阳性成人肝癌筛查监测培训(星光项目)"),
    (r"慢性乙型肝炎病毒感染者肝细胞癌筛查和监测", "慢乙肝病毒感染者HCC筛查和监测(指南解读)"),
    (r"特殊群体的疫苗接种|乙肝疫苗使用指南", "乙肝疫苗使用指南特殊群体接种"),
    (r"机会性筛查|急诊.*筛查|门诊.*筛查|血站.*筛查", "乙肝机会性筛查场景研究"),
    (r"扩大筛查|扩大检测|全民筛查", "乙肝扩大筛查检测研究"),
    (r"知晓率|检测率.*调查|HBsAg阳性.*知晓", "乙肝检测率知晓率调查"),
]

# ---------- 归并 ----------
def merge(records):
    """records: list of (topic, media, date, title, prio, rule, year)
    返回: OrderedDict 实体名 -> {次数, 优先级集, 年份集, 来源列表, 代表条目}"""
    merged = OrderedDict()
    for r in records:
        title = r[3]
        matched = None
        for pat, name in ENTITIES:
            if re.search(pat, title):
                matched = name
                break
        key = matched or clean_title(title)
        if key not in merged:
            merged[key] = {"count": 0, "prios": set(), "years": set(),
                           "media": set(), "sample": r}
        merged[key]["count"] += 1
        merged[key]["prios"].add(r[4])
        merged[key]["years"].add(r[6])
        merged[key]["media"].add(r[1])
    return merged

def _prio_key(x):
    try:
        return int(x[1:])
    except (ValueError, IndexError):
        return 99

# 溯源台账表头：专题, 实体名, 出现次数, 最高优先级, 年份, 来源媒体, 代表候选标题, 溯源状态, PMID, DOI, 期刊年卷期, 官方链接, 剔除原因/备注
LEDGER_HEADER = ["专题", "实体名", "出现次数", "最高优先级", "年份", "来源媒体",
                 "代表候选标题", "溯源状态", "PMID", "DOI", "期刊年卷期", "官方链接", "剔除原因/备注"]

def main():
    topics = sys.argv[1:] if len(sys.argv) > 1 else []
    rows = list(csv.reader(io.open(CSV_PATH, encoding="utf-8-sig")))
    header, data = rows[0], rows[1:]
    if not topics:
        topics = sorted({r[0] for r in data})
    out_dir = os.path.join(BASE, "台账")
    os.makedirs(out_dir, exist_ok=True)
    ledger_path = os.path.join(out_dir, "溯源台账.csv")
    ledger_existed = os.path.exists(ledger_path)
    ledger_rows = list(csv.reader(io.open(ledger_path, encoding="utf-8-sig"))) if ledger_existed else []
    ledger_header = ledger_rows[0] if ledger_rows else LEDGER_HEADER
    existing = {}
    for r in ledger_rows[1:]:
        if len(r) >= 2:
            existing.setdefault(r[0], {})[r[1]] = r
    summary = []
    for t in topics:
        pool = [r for r in data if r[0] == t]
        merged = merge(pool)
        print("=" * 60)
        print("{}：候选 {} 条 → 唯一文献 {} 篇（去重后）".format(t, len(pool), len(merged)))
        print("=" * 60)
        topic_rows = existing.get(t, {})
        for i, (k, v) in enumerate(merged.items(), 1):
            prios = "".join(sorted(v["prios"], key=_prio_key))
            top = prios[0] if prios else "?"
            yrs = "、".join(sorted(v["years"], reverse=True))
            sample = v["sample"][3]
            print("{:3d}. [P{}] 出现{}次 {} | {}".format(i, top, v["count"], k, sample[:40]))
            # 保留已有台账行（含溯源状态），新实体填入默认状态
            if k not in topic_rows:
                topic_rows[k] = [t, k, v["count"], top, yrs, ",".join(sorted(v["media"])),
                                 sample, "待核实", "", "", "", "", ""]
        existing[t] = topic_rows
        summary.append((t, len(pool), len(merged)))
    # 写回台账（保留旧行，追加新行；按专题顺序输出）
    with io.open(ledger_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(ledger_header)
        for t in topics:
            for r in existing.get(t, {}).values():
                w.writerow(r)
    print("\n台账已写入: {}".format(ledger_path))
    for t, n, u in summary:
        print("{}: {} → {}".format(t, n, u))

if __name__ == "__main__":
    main()
