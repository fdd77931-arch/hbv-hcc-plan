# -*- coding: utf-8 -*-
"""
第12批回填：T4B_临床治愈 专题溯源核实（88 条）
锁定 3 条（PMID/DOI 均经 PubMed/WebSearch 验证）
剔除 85 条（期刊导读/病例分享/会议速递/访谈/项目报道等）
子串匹配 + 全量写回；未命中条目中止写回，防台账污染
"""
import csv
import sys

LEDGER = '台账/溯源台账.csv'

# ---- 锁定列表：子串 -> (PMID, DOI, 期刊年卷期, 官方链接, 备注) ----
LOCK = [
    ("基线Th17和Treg细胞水平", "39958952", "10.1016/j.livres.2023.04.002",
     "Liver Res 2023,7(2):136-144",
     "https://pubmed.ncbi.nlm.nih.gov/39958952/",
     "吴丽丽/高志良团队（中山三院感染科），CCI模型AUC 0.957"),
    ("血清RANTES早期下降", "34371537", "10.3760/cma.j.cn501113-20210706-00322",
     "中华肝脏病杂志 2021,29(7):666-672",
     "https://pubmed.ncbi.nlm.nih.gov/34371537/",
     "贾瑞/王福生/福军亮（解放军总医院第五医学中心），12周RANTES下降可预测48周HBsAg清除"),
    ("聚乙二醇干扰素序贯核苷类似物治疗HBeAg阳性", "32990919", "10.1007/s12072-020-10095-1",
     "Hepatol Int 2021,15(1):51-59",
     "https://pubmed.ncbi.nlm.nih.gov/32990919/",
     "徐伟/李强/陈良（上海公卫临床中心），临床肝胆病杂志摘译转载，锁定英文原文"),
]

# ---- 剔除列表：子串 -> 剔除原因（按序匹配，靠前者优先） ----
EXCL = [
    ("南月敏教授：慢乙肝核苷", "非期刊来源：会议讲座整理稿（2020 EASL 肝愈之道公开课，非正式论文）"),
    ("全球最大乙肝临床治愈研究队列", "非期刊来源：项目会议报道（珠峰2025管理工作会议；项目正式论文见珠峰CGH PMID 41638418）"),
    ("家系无忧", "非期刊来源：项目启动报道（真实世界研究项目）"),
    ("容愈项目", "非期刊来源：项目进展报道（正式数据见APASL2025容愈摘要 OP0395）"),
    ("启动培训会", "非期刊来源：项目活动报道"),
    ("我国多个乙肝临床治愈研究项目发布最新成果", "非期刊来源：媒体综合报道（肝博士）"),
    ("李海：哪些患者可追求慢乙肝的临床治愈", "非期刊来源：专家访谈/科普（肝癌在线）"),
    ("国际多中心研究：核苷如何停药", "非中国证据：国际多中心研究报道"),
    ("AASLD中国之声", "非期刊来源：国际会议报道（AASLD）"),
    ("APASL2025", "非期刊来源：国际会议报道（APASL2025）"),
    ("速递", "非期刊来源：国际会议报道（AASLD/EASL/APASL）"),
    ("愈见乙肝", "非期刊来源：病例分享（愈见乙肝系列）"),
    ("临床治愈集结号", "非期刊来源：病例分享（临床治愈集结号系列）"),
    ("名家访谈", "非期刊来源：专家访谈"),
    ("期刊导读", "非原始文献：期刊导读（雨露肝霖）"),
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
    rows = list(csv.reader(open(LEDGER, encoding='utf-8')))
    header, data = rows[0], rows[1:]
    if not header or header[7] != '溯源状态':
        print('表头异常，中止'); sys.exit(1)

    n_lock = n_excl = 0
    unhandled = []
    t4b_idx = [i for i, r in enumerate(data) if r[0] == 'T4B_临床治愈']
    for i in t4b_idx:
        r = data[i]
        if r[7] != '待核实':
            continue  # 幂等：已处理的跳过
        ent = r[1]
        # 1) 尝试锁定
        lock = find_lock(ent)
        if lock:
            r[7] = '已锁定'
            r[8], r[9], r[10], r[11], r[12] = lock
            n_lock += 1
            continue
        # 2) 尝试剔除
        reason = find_excl(ent)
        if reason:
            r[7] = '已剔除'
            r[8], r[9], r[10], r[11] = '', '', '', ''
            r[12] = reason
            n_excl += 1
            continue
        unhandled.append((i + 2, ent))  # +2 转 CSV 行号（含表头）

    if unhandled:
        print(f'未处理 {len(unhandled)} 条，中止写回：')
        for idx, ent in unhandled:
            print(f'  行{idx} {ent}')
        sys.exit(1)

    with open(LEDGER, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(data)

    print(f'第12批回填完成：T4B 已锁定 {n_lock} 条 / 已剔除 {n_excl} 条')


if __name__ == '__main__':
    main()
