# -*- coding: utf-8 -*-
"""
第13批：T4C_干扰素专题回填脚本
策略：LOCK 列表（子串→PMID/DOI/期刊/链接/备注）+ EXCL 列表（子串→剔除原因）
find_lock / find_excl 用 sub in ent 子串匹配
未处理条目 raise SystemExit 中止写回，防台账污染
先干运行（DRY=1）验证全部命中后再实跑（DRY=0）
"""
import csv, sys

CSV = '台账/溯源台账.csv'
TOPIC = 'T4C_干扰素'
DRY = int(sys.argv[1]) if len(sys.argv) > 1 else 1  # 1=干运行 0=实跑

# (子串, PMID, DOI, 期刊年卷期, 官方链接, 备注)
LOCK = [
    ("【共识】慢性乙型肝炎临床治愈", "", "10.3760/cma.j.issn.1000-6680.2019.08.003",
     "中华传染病杂志 2019,37(8):461-472（同步刊发于临床肝胆病杂志 2019,35(8):1693-1701, DOI 10.3969/j.issn.1001-5256.2019.08.008）",
     "https://rs.yiigle.com/cmaid/1191995",
     "中华医学会感染病学分会/肝病学分会 2019 专家共识，T4C 核心共识文献"),
    ("TMF治疗慢性乙型肝炎的疗效与安全性", "40078202", "10.14218/JCTH.2024.00364",
     "J Clin Transl Hepatol 2025,13(3):207-215（中文版见中华肝脏病杂志 2025）",
     "https://www.xiahepublishing.com/journal/jcth",
     "党双锁团队 TMF 真实世界多中心研究，英文原文 JCTH，中文版转载中华肝脏病杂志"),
    ("慢性乙型肝炎临床治愈的中国实践", "", "10.3760/cma.j.cn501113-20240325-00156",
     "中华肝脏病杂志 2024,32(5):411-417（专家论坛）",
     "https://rs.yiigle.com/cmaid/1461108",
     "莫志硕、谢冬英、林炳亮、窦晓光、万谟彬、江家骥、赵英仁、唐红、庄辉、高志良 专家论坛"),
    ("常楚笛南月敏", "", "10.3760/cma.j.cn501113-20230322-00124",
     "中华肝脏病杂志 2023,31(8):855-861",
     "https://rs.yiigle.com/cmaid/1450652",
     "常楚笛/南月敏 河北医科大学第三医院 TAF/TDF/ETV 一线药物真实世界研究"),
    ("许红梅", "", "10.3760/cma.j.cn501113-20210225-00094",
     "中华肝脏病杂志 2022,30(10):1056-1062",
     "https://rs.yiigle.com/cmaid/1447892",
     "王慧敏/周英芝/许红梅（重庆医科大学附属儿童医院）Peg-IFNα-2a vs ETV 儿童真实世界研究"),
    ("宿主基因多态", "", "10.14218/JCTH.2022.00057",
     "J Clin Transl Hepatol 2023,11(2):295-303（中文版见中华肝脏病杂志 2022）",
     "https://www.xiahepublishing.com/m/2310-8819/JCTH-2022-00057",
     "陈佳旋/蒋德科（南方医科大学南方医院）CD55 基因多态预测 Peg-IFNα 应答"),
    ("党双锁：干扰素α治疗慢性乙型肝炎患者获得HBsAg血清学转换后HBeAg阳性4例", "", "10.3760/cma.j.cn501113-20200318-00123",
     "中华肝脏病杂志 2021,29(6):580-582",
     "https://rs.yiigle.com/cmaid/1447923",
     "吴凤萍/党双锁（西安交大二附院）HBsAg 血清学转换后 HBeAg 阳性 4 例病例分析"),
    ("干扰素治疗B、C基因型", "", "10.3969/j.issn.1001-5256.2019.06.015",
     "临床肝胆病杂志 2019,35(6):1256-1261",
     "https://lcgdbzz.org/article/id/LCGD201906018",
     "李敏/单姗/吴晓宁/尤红/贾继东（北京友谊医院）B/C 基因型 IFN 疗效差异 Meta 分析"),
    ("庄辉院士：慢性乙型肝炎功能性治愈不是梦", "", "10.12449/JCH250101",
     "临床肝胆病杂志 2025,41(1):2-6（述评）",
     "https://lcgdbzz.org/cn/article/doi/10.12449/JCH250101",
     "庄辉院士述评：功能性治愈定义、优势人群策略与新药进展"),
    ("褚萨萨高峰", "", "10.3760/cma.j.cn501113-20240829-00402",
     "中华肝脏病杂志 2024,32(10):904-909",
     "https://rs.yiigle.com/cmaid/1447923",
     "褚萨萨/高峰（临沂市人民医院）TMF 治疗 65 岁以上 CHB 及肝硬化患者真实世界研究"),
    ("干扰素刺激基因", "", "10.3969/j.issn.1001-5256.2022.01.031",
     "临床肝胆病杂志 2022,38(1):180-186",
     "https://lcgdbzz.org/cn/article/doi/10.3969/j.issn.1001-5256.2022.01.031",
     "练韵文/郑杏容/吴和维/高志良/陈希瑶/谢婵（中山三院）干扰素刺激基因抗HBV感染研究进展综述"),
]

# (子串, 剔除原因)
EXCL = [
    ("【期刊导读】", "期刊导读（雨露肝霖栏目），非原始文献"),
    ("【临床治愈集结号】", "病例分享（临床治愈集结号栏目），非原始文献"),
    ("【愈见乙肝", "病例分享/患者故事（愈见乙肝栏目），非原始文献"),
    ("【AASLD", "国际会议速递（AASLD），非原始文献"),
    ("【APASL", "国际会议速递/会议摘要（APASL），非原始文献"),
    ("【EASL", "国际会议速递/会议摘要（EASL），非原始文献"),
    ("AASLD20", "国际会议报道（AASLD），非原始文献"),
    ("EASL20", "国际会议报道/会议摘要（EASL），非原始文献"),
    ("【会议撷萃】", "会议报告整理（会议撷萃栏目），非原始文献"),
    ("【名家访谈】", "专家访谈（名家访谈栏目），非期刊来源"),
    ("【中国派名家访谈】", "专家访谈（中国派栏目），非期刊来源"),
    ("【数据阅独】", "流行病学数据分析科普（数据阅独栏目），非原始文献"),
    ("【新药进展】", "新药研发进展报道（国外研究），非中国证据"),
    ("【临床治愈相关争议探讨】", "专家观点讨论（争议探讨栏目），非期刊来源"),
    ("NEJM：Xalnesiran", "国外文献导读（NEJM Xalnesiran 研究），非中国证据/非原始文献"),
    ("J Hepatol：儿童和青少年HCV感染", "国外文献导读（J Hepatol 英国 HCV 研究）且非 HBV 专题，非中国证据"),
    ("全国多中心项目：干扰素治疗代偿期乙肝肝硬化安全性研究招募", "项目招募信息，非期刊来源"),
    ("中文版来了", "共识转载（与【共识】条目同文），重复剔除"),
    ("干扰素抗HBV治疗实现临床治愈", "专家观点/科普（肝胆相照平台），非期刊来源"),
    ("病毒性肝炎：乙肝干扰素治疗停药时机", "专家讲座整理（肝胆相照平台），非期刊来源"),
    ("慢性乙型肝炎临床治愈170例分析", "临床经验总结（肝胆相照平台），无期刊出处可溯，非期刊来源"),
    ("谢尧教授", "专家讲座（肝胆相照平台温故知新栏目），非期刊来源"),
    ("为什么干扰素治疗后，HBsAg水平反而更高了", "媒体科普（肝博士），非期刊来源"),
    ("儿童慢性乙型肝炎患者基于干扰素治疗策略的临床治愈之路", "述评转载（雨露肝霖「转」述评），非原始文献"),
    ("PD-1抗体联合干扰素", "EASL 会议数据报道，非原始文献"),
    ("Xalnesiran", "新药（siRNA）研发报道，国外研究非中国证据"),
    ("APASL20", "国际会议报道/会议摘要（APASL），非原始文献"),
    ("JHepatol：儿童和青少年HCV感染", "国外文献导读（J Hepatol 英国 HCV 研究）且非 HBV 专题，非中国证据"),
    ("【Hepatology】", "期刊导读（Hepatology 杂志研究解读），非原始文献"),
    ("【肝霖特写丨", "科普特写（肝霖特写栏目），非期刊来源"),
    ("孕妇开展抗病毒治疗的时间选择", "专家讲座整理（肝胆相照平台），非期刊来源"),
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

    print(f"T4C 待核实条目: {len([r for r in data if r[0]==TOPIC and r[7]=='待核实'])}")
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
