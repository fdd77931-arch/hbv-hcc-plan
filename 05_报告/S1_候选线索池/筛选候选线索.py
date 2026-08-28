# -*- coding: utf-8 -*-
"""
S1 线索采集：候选线索筛选脚本
输入：各专题 *_ima原始线索.txt（每行：来源媒体_YYYY-MM-DD_标题.pdf）
输出：
  1. 候选线索台账 CSV（全部通过初筛的线索，含专题/来源/日期/标题/优先级）
  2. 候选线索清单 md（按专题分组的优选候选，供人工审核）
"""
import csv
import io
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
OUT_ROOT = os.path.dirname(BASE)  # 05_报告
TARGET_CSV = os.path.join(BASE, "候选线索台账.csv")
TARGET_MD = os.path.join(BASE, "候选线索清单_初筛.md")

# ---------- 专题配额（500 篇目标，S0 已建 10 篇 → 剩余 490 篇）----------
QUOTA_LEFT = {
    "T1_指南政策": 58, "T2_筛查": 59, "T3_治疗策略": 68,
    "T4A_初治": 45, "T4B_临床治愈": 44, "T4C_干扰素": 60,
    "T4D_新药研发": 24, "T4E_联合方案": 34, "T5_肝癌早筛": 43,
    "T6_长期管理": 25, "T7_联盟建设": 30,
}

# ---------- 排除规则：低价值/非学术线索 ----------
EXCLUDE_PATTERNS = [
    r"会议(通知|预告|日程|报名)", r"直播(预告)?", r"课程预告", r"学术会议",
    r"病例征集", r"问卷调研", r"邀您加入", r"招聘|招人", r"有奖",
    r"大降价|降价|价格", r"执行价", r"最低价", r"分散片",  # 药品价格资讯
    r"直播回放", r"视频回顾", r"回看", r"PPT下载", r"幻灯下载",
    r"明日直播|今日直播|今晚", r"预告", r"精彩预告",
    r"获奖|评审结果|入围", r"榜单", r"投票",
    r"科普|一图看懂|一文详知|一文看懂|必知|详解",  # 纯科普推文（区别于期刊导读）
    r"招聘启事", r"会议报道", r"圆满(落幕|结束|举办|召开)", r"启动会",  # 会议报道类（保留项目正式启动等政策类）
]
# 但以下情况例外：会议报道中含"项目启动/官方通知"的政策性内容保留
EXCLUDE_EXCEPTIONS = [
    r"项目(正式)?启动", r"申报工作的通知", r"官方", r"规范化建设与能力提升项目",
    r"指南实践工程", r"专项", r"联盟(成立|启动)", r"行动计划", r"防治指南实践",
]

# ---------- 优先级加分规则 ----------
PRIORITY_KEYWORDS = {
    0: [  # P0：国家级指南/政策/共识/官方文件
        r"防治指南.*(版|年版)", r"专家共识", r"专家建议", r"官方",
        r"WHO|世界卫生组织", r"健康中国2030", r"消除(病毒性)?肝炎", r"行动计划",
        r"指南.*解读", r"更新要点", r"英文版正式发表",
    ],
    1: [  # P1：高质量证据（RCT/荟萃/真实世界/期刊）
        r"荟萃分析|系统评价|Meta", r"随机", r"真实世界", r"队列",
        r"期刊导读", r"外刊精读", r"NEJM|Lancet|J Hepatol|Gastroenterology|Hepatology|JOH|JCTH",
        r"临床治愈", r"HBsAg(清除|阴转|血清学转换)", r"国际多中心",
        r"全国.*研究", r"中国.*研究", r"多中心",
    ],
    2: [  # P2：专家论坛/述评/病例报告
        r"专家论坛", r"述评", r"学术争鸣", r"专家访谈|名家访谈|大咖",
        r"愈见乙肝", r"临床治愈集结号", r"肝霖特写",
    ],
}

# ---------- 解析文件名 ----------
def parse_line(line):
    """解析：媒体_YYYY-MM-DD_标题.pdf → (media, date, title)"""
    line = line.strip()
    # 移除 .pdf 后缀
    title_full = re.sub(r"\.pdf$", "", line)
    m = re.match(r"^(.*?)_(\d{4}-\d{2}-\d{2})_(.*)$", title_full)
    if m:
        media, date, title = m.group(1), m.group(2), m.group(3)
    else:
        media, date, title = "未知来源", "未知日期", title_full
    return media, date, title

def year_from_date(date):
    m = re.match(r"(\d{4})", date)
    return int(m.group(1)) if m else 0

def is_excluded(title, date):
    year = year_from_date(date)
    # 2018 及更早：仅保留指南/共识/里程碑研究（奠基性）
    if 0 < year <= 2018:
        if not re.search(r"指南|共识|专家建议|JAMA|Hepatology|J Hepatol|Gastroenterology|荟萃|队列|多中心", title):
            return True
    for pat in EXCLUDE_PATTERNS:
        if re.search(pat, title):
            # 检查例外
            if any(re.search(e, title) for e in EXCLUDE_EXCEPTIONS):
                return False
            return True
    return False

def score_priority(title):
    """返回 (优先级, 命中规则)"""
    for p in (0, 1, 2):
        for pat in PRIORITY_KEYWORDS[p]:
            if re.search(pat, title):
                return p, pat
    return 3, "未命中"

# ---------- 主流程 ----------
records = []  # (专题, media, date, title, priority, rule, year)
# ---------- 专题别名映射（文件名归一化到正式专题）----------
TOPIC_MAP = {
    "T1_指南政策": "T1_指南政策", "T2_筛查": "T2_筛查", "T3_治疗策略": "T3_治疗策略",
    "T4A_初治": "T4A_初治", "T4B_临床治愈": "T4B_临床治愈", "T4C_干扰素": "T4C_干扰素",
    "T4D_新药研发": "T4D_新药研发", "T4E_联合方案": "T4E_联合方案",
    "T4E_新药研发": "T4E_联合方案",  # 第二轮新药检索并入 T4E
    "T5_肝癌早筛": "T5_肝癌早筛", "T6_长期管理": "T6_长期管理", "T7_联盟建设": "T7_联盟建设",
    "T4D_新药研发_b": "T2_筛查",  # 母婴阻断线索并入筛查/预防
    "T2_筛查_c": "T2_筛查",       # 疫苗接种线索并入筛查/预防
}

for fname in sorted(os.listdir(BASE)):
    if not fname.endswith("_ima原始线索.txt"):
        continue
    raw_topic = fname.replace("_ima原始线索.txt", "")
    # 归一化专题名：优先按完整文件名映射（含 _b/_c 后缀），再按去后缀名映射
    topic = TOPIC_MAP.get(raw_topic) or TOPIC_MAP.get(re.sub(r"_[bc]$", "", raw_topic)) or raw_topic
    # 未收录专题名的防御：跳过（避免统计崩溃）
    if topic not in QUOTA_LEFT:
        print("⚠️  跳过未知专题: {} (来自 {})".format(topic, fname))
        continue
    path = os.path.join(BASE, fname)
    with io.open(path, "r", encoding="utf-8") as f:
        for line in f:
            media, date, title = parse_line(line)
            if not title:
                continue
            if is_excluded(title, date):
                continue
            prio, rule = score_priority(title)
            records.append((topic, media, date, title, prio, rule, year_from_date(date)))

# 去重（同一标题跨专题重复出现，保留第一个专题归属）
seen = set()
uniq = []
for rec in records:
    if rec[3] in seen:
        continue
    seen.add(rec[3])
    uniq.append(rec)
records = uniq

# 输出统计
print("=" * 70)
print("初筛通过线索总数：{} 条（原始 2300 条 = 11+12 轮检索）".format(len(records)))
print("=" * 70)
from collections import Counter
tc = Counter(r[0] for r in records)
for topic, n in sorted(tc.items()):
    quota = QUOTA_LEFT.get(topic, "?")
    print("  {:16s} {:3d} 条  | 剩余配额 {:>2d} | 候选/配额 {:.1f}x".format(topic, n, quota, n / quota if quota else 0))

# 写入 CSV 台账
with io.open(TARGET_CSV, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["专题", "线索来源媒体", "日期", "标题", "优先级P", "命中规则", "年份"])
    for rec in sorted(records, key=lambda r: (r[0], r[4], -r[6])):
        w.writerow(list(rec))

# 写入 md 清单
with io.open(TARGET_MD, "w", encoding="utf-8") as f:
    f.write("# S1 候选线索清单（初筛）\n\n")
    f.write("> 来源：ima「肝斗士-肝脏修复」知识库 11 次专题检索（每专题 100 条）\n")
    f.write("> 初筛规则：排除会议通知/直播预告/药品价格/纯科普/2018 前非奠基文献；P0-P2 优先排序\n\n")
    f.write("| 专题 | 剩余配额 | 初筛候选数 |\n|---|---|---|\n")
    for topic, n in sorted(tc.items()):
        f.write("| {} | {} | {} |\n".format(topic, QUOTA_LEFT.get(topic, "?"), n))
    f.write("\n---\n\n")
    cur_topic = None
    for rec in sorted(records, key=lambda r: (r[0], r[4], -r[6])):
        topic, media, date, title, prio, rule, year = rec
        if topic != cur_topic:
            cur_topic = topic
            f.write("\n## {}（配额 {}/{}）\n\n".format(topic, QUOTA_LEFT.get(topic, "?"), len(tc)))
            f.write("| P | 日期 | 标题 | 来源 |\n|---|---|---|---|\n")
        f.write("| P{} | {} | {} | {} |\n".format(prio, date, title, media))

print("\n已输出：\n  {}\n  {}".format(TARGET_CSV, TARGET_MD))
