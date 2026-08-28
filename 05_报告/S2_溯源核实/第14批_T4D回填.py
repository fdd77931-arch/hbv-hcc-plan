# -*- coding: utf-8 -*-
"""
第14批：T4D_新药研发专题回填脚本
策略：LOCK 列表（子串→PMID/DOI/期刊/链接/备注）+ EXCL 列表（子串→剔除原因）
find_lock / find_excl 用 sub in ent 子串匹配
未处理条目 raise SystemExit 中止写回，防台账污染
先干运行（DRY=1）验证全部命中后再实跑（DRY=0）
"""
import csv, sys

CSV = '台账/溯源台账.csv'
TOPIC = 'T4D_新药研发'
DRY = int(sys.argv[1]) if len(sys.argv) > 1 else 1  # 1=干运行 0=实跑

# (子串, PMID, DOI, 期刊年卷期, 官方链接, 备注)
LOCK = [
    ("经治患者抗病毒治疗专家共识", "", "",
     "中华实验和临床感染病杂志(电子版) 2016,10(5):527-533",
     "https://lcgdbzz.org/en/custom/news/id/8246",
     "慢性乙型肝炎核苷(酸)类似物经治患者抗病毒治疗专家委员会 2016 年更新版共识（2013 版更新），经治患者管理纲领性文件"),
    ("AHB-137用药12周", "", "10.1007/s12072-026-11102-7",
     "Hepatol Int 2026（AB-10-8002, NCT06115993）",
     "https://link.springer.com/article/10.1007/s12072-026-11102-7",
     "浩博医药 AHB-137 中国 1a/1b 期研究：12 周 HBsAg 清除率 62%（300mg 组）/43%（225mg 组），AASLD2024 会议数据 2026 年全文发表"),
    ("乙型肝炎功能性治愈新药——", "", "10.12449/JCH250102",
     "临床肝胆病杂志 2025,41(1):7-14",
     "https://lcgdbzz.org/cn/article/doi/10.12449/JCH250102",
     "梁携儿/刘智泓/侯金林（南方医院感染内科）专家论坛：ASO 与小干扰 RNA 新药全景"),
    ("丁艳华", "", "10.3969/j.issn.1001-5256.2021.05.003",
     "临床肝胆病杂志 2021,37(5):1006-1010",
     "https://lcgdbzz.org/article/lcgdbzz/2021/5/1006",
     "张洪/朱晓雪/丁艳华（吉林大学第一医院 I 期临床试验病房）CHB 抗病毒新药临床研究综述"),
    ("反义寡核苷酸治疗慢性乙肝", "", "10.3760/cma.j.cn501113-20221127-00577",
     "中华肝脏病杂志 2023,31(2):192-197",
     "https://rs.yiigle.com/cmaid/1447923",
     "李德瑶/陆丹娟/鲁凤民（北京大学）ASO 治疗 CHB 述评：相对确定的有限疗效与尚未明确的机制"),
]

# (子串, 剔除原因)
EXCL = [
    ("EASL20", "国际会议报道/会议摘要（EASL），非原始文献"),
    ("AASLD20", "国际会议报道/会议摘要（AASLD），非原始文献"),
    ("APASL20", "国际会议报道/会议摘要（APASL），非原始文献"),
    ("Bulevirtide", "国外新药（HDV 病毒进入抑制剂）研究报道，非中国证据/非 HBV 专题"),
    ("AHB-137", "新药管线动态/会议报道（AHB-137 各阶段进展），非原始文献"),
    ("Bepirovirsen", "国外新药（GSK ASO）管线动态报道，非中国证据"),
    ("AssemblyBio", "国外新药管线动态（Assembly Bio），非中国证据"),
    ("特宝生物", "企业合作研发新闻（Aligos/特宝生物），非期刊来源"),
    ("HRS-5635", "新药管线动态（恒瑞医药 siRNA），非原始文献"),
    ("EDP-514", "国外新药（核心蛋白抑制剂）数据发表报道，非中国证据"),
    ("乙型肝炎功能性治愈新药—聚焦", "与锁定条目同文转载（肝胆相照平台「转」），重复剔除"),
    ("鲁凤民：反义寡核苷酸治疗慢性乙型肝炎", "与锁定条目同文（中华肝脏病杂志公众号学术前沿栏目），重复剔除"),
    ("抗病毒治疗HBsAg清除后复阳", "国外文献导读（Gut 2020 韩国全国多中心研究微述评，片警实验室栏目），非中国证据/非原始文献"),
    ("慢乙肝抗病毒治疗的初始治疗", "专家观点讨论（肝胆相照平台学术争鸣栏目），非期刊来源"),
    ("中药联合抗病毒药物治疗乙肝肝硬化", "专家讲座/科普（肝胆相照平台），非期刊来源"),
    ("核苷酸酶偏高", "媒体科普（肝病知识），非期刊来源"),
    ("新型冠状病毒感染抗病毒药物引起肝损伤", "非专题：新冠抗病毒药物肝损伤机制（非乙肝新药）"),
    ("直接抗病毒药物治疗丙型肝炎", "非专题：丙肝 DAA 治疗失败影响因素（非乙肝新药）"),
    ("慢乙肝患者应用抗病毒药物就不会得肝癌了吗", "科普/访谈转载（肝癌在线），非期刊来源"),
    ("张翀：妊娠期服用抗病毒药物", "专家访谈（肝癌在线），非期刊来源"),
    ("免疫检查点抑制剂或可引发乙肝病毒再激活", "国外研究新闻编译（肝脏时间），非中国证据"),
]


def find_lock(ent):
    for sub, pmid, doi, j, link, note in LOCK:
        if sub in ent:
            return (pmid, doi, j, link, note)
    return None


def find_excl(ent):
    for sub, reason in EXCL:
        if sub in ent:
            return reason
    return None


def main():
    with open(CSV, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    header, data = rows[0], rows[1:]

    unmatched = []
    lock_hits, excl_hits = [], []
    for i, r in enumerate(data):
        if r[0] != TOPIC or r[7] != '待核实':
            continue
        ent = r[1]
        lk = find_lock(ent)
        if lk:
            lock_hits.append((i, ent, lk))
            continue
        ex = find_excl(ent)
        if ex:
            excl_hits.append((i, ent, ex))
            continue
        unmatched.append((i, ent))

    print(f"T4D 待核实条目: {len([r for r in data if r[0]==TOPIC and r[7]=='待核实'])}")
    print(f"LOCK 命中: {len(lock_hits)} 条")
    print(f"EXCL 命中: {len(excl_hits)} 条")
    print(f"未匹配: {len(unmatched)} 条")

    for i, ent in unmatched:
        print(f"  未匹配[{i}]: {ent}")

    if unmatched:
        print("存在未匹配条目，中止写回！")
        raise SystemExit(1)

    if DRY:
        print("\n[干运行] 验证通过，未写回。用 DRY=0 实跑。")
        for i, ent, lk in lock_hits:
            print(f"  LOCK[{i}]: {ent[:40]} -> {lk[1]}")
        return

    # 实跑写回
    n_lock = n_excl = 0
    for i, ent, (pmid, doi, j, link, note) in lock_hits:
        r = data[i]
        r[7] = '已锁定'
        r[8], r[9], r[10], r[11], r[12] = pmid, doi, j, link, note
        n_lock += 1
    for i, ent, reason in excl_hits:
        r = data[i]
        r[7] = '已剔除'
        r[12] = reason
        n_excl += 1

    with open(CSV, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(data)
    print(f"\n[实跑] 写回完成：已锁定 {n_lock} 条 / 已剔除 {n_excl} 条")


if __name__ == '__main__':
    main()
