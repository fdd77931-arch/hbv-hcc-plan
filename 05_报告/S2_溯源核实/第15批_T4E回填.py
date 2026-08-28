# -*- coding: utf-8 -*-
"""
第15批：T4E_联合方案专题回填脚本
策略：LOCK 列表（子串→PMID/DOI/期刊/链接/备注）+ EXCL 列表（子串→剔除原因）
find_lock / find_excl 用 sub in ent 子串匹配
未处理条目 raise SystemExit 中止写回，防台账污染
先干运行（DRY=1）验证全部命中后再实跑（DRY=0）
"""
import csv, sys

CSV = '台账/溯源台账.csv'
TOPIC = 'T4E_联合方案'
DRY = int(sys.argv[1]) if len(sys.argv) > 1 else 1  # 1=干运行 0=实跑

# (子串, PMID, DOI, 期刊年卷期, 官方链接, 备注)
LOCK = [
    ("非一线核苷", "", "10.3969/j.issn.1001-5256.2019.06.008",
     "临床肝胆病杂志 2019,35(6):1212-1214",
     "https://lcgdbzz.org/article/id/LCGD201906008",
     "中华医学会肝病学分会肝炎学组：非一线NAs经治CHB患者治疗策略调整专家共识（2019）"),
    ("NQO1抑制剂Dicoumarol", "32987030", "10.1016/j.jhep.2020.09.019",
     "J Hepatol 2021,74(3)",
     "https://pubmed.ncbi.nlm.nih.gov/32987030/",
     "重庆医科大学黄爱龙/陈娟团队：双香豆素（NQO1抑制剂）促HBx降解阻断cccDNA转录（程胜桃一作）"),
    ("TDF序贯加用干扰素", "34228855", "10.1111/jvh.13571",
     "J Viral Hepat 2021,28(10)",
     "https://pubmed.ncbi.nlm.nih.gov/34228855/",
     "瑞金医院张欣欣团队牵头7中心（NCT03013556）：TDF序贯加用Peg-IFNα提高HBeAg阳性初治患者HBsAg清除率"),
    ("衣壳组装调节剂联合核苷", "", "10.3969/j.issn.1001-5256.2022.08.001",
     "临床肝胆病杂志 2022,38(8):1705-1709",
     "https://lcgdbzz.org/cn/article/doi/10.3969/j.issn.1001-5256.2022.08.001",
     "鲁凤民/黄鸿鑫/毛天皓/陈香梅/庄辉（北京大学人民医院/北大医学部）述评：CpAM联合NUC临床试验科学问题"),
    ("核苷酸类似物更能提高", "32410175", "",
     "J Gastrointest Surg 2021,25(6):1419-1429",
     "https://pubmed.ncbi.nlm.nih.gov/32410175/",
     "华西医院文天夫/严律南团队：NtA较NsA显著降低HBV相关HCC根治术后复发并改善总生存"),
]

# (子串, 剔除原因)
EXCL = [
    ("APASL2025", "国际会议报道（APASL2025），非原始文献"),
    ("APASL2023", "国际会议报道（APASL2023），非原始文献"),
    ("AASLD2019", "国际会议报道（AASLD2019），非原始文献"),
    ("AASLD2021", "国际会议报道（AASLD2021），非原始文献"),
    ("AASLD2023", "国际会议报道（AASLD2023），非原始文献"),
    ("EASL2021", "国际会议报道（EASL2021），非原始文献"),
    ("EASL2022", "国际会议报道（EASL2022），非原始文献"),
    ("EASL2024", "国际会议报道（EASL2024），非原始文献"),
    ("EASL2025", "国际会议报道（EASL2025），非原始文献"),
    ("HEPDART2021", "国际会议报道（HEPDART2021），非原始文献"),
    ("愈见乙肝", "病例分享栏目（愈见乙肝2024），非期刊来源"),
    ("非酒精性脂肪性肝病影响", "期刊导读（NAFLD影响NAs疗效），非原始文献"),
    ("核苷序贯联合PEGIFNα", "期刊导读（核苷序贯联合PEG IFNα-2b），非原始文献"),
    ("接受免疫检查点抑制剂治疗的癌症患者", "国外文献导读（J Hepatol 肝癌患者乙肝功能性治愈），非中国证据/非原始文献"),
    ("免疫检查点抑制剂治疗可能有助于HBsAg阳性", "期刊导读（ICIs助HBsAg阳性癌症患者乙肝临床治愈），非原始文献"),
    ("ccc_R08", "国外新药管线动态（罗氏ccc_R08），非中国证据"),
    ("干扰素α联合PD-1抗体", "期刊导读（IFNα联合PD-1治疗肝癌），非原始文献"),
    ("郑素军教授", "专家访谈（肝癌在线），非期刊来源"),
    ("SWAP研究", "国际研究导读（SWAP研究联合vs序贯），非中国证据/非原始文献"),
    ("HBsAg血清学清除能够进一步降低", "国外文献导读（J Hepatol），非中国证据"),
    ("Endeavor研究", "期刊导读（Endeavor研究），非原始文献"),
    ("施国明", "非专题（胆道系统恶性肿瘤ICIs治疗，非乙肝联合方案）"),
    ("这些检查你必须知道", "科普（ICIs治疗前检查），非期刊来源"),
    ("Rencofilstat", "国外新药管线动态（Rencofilstat 2b期终止），非中国证据"),
    ("揭秘检查点抑制剂引发肝损伤", "名家专访（Guruprasad P. Aithal），非期刊来源"),
    ("质子泵抑制剂治疗是失代偿期肝硬化患者发生慢加急性肝衰竭", "学术前沿导读（Hepatol Commun）+非专题（ACLF危险因素）"),
    ("ABI-43341b期", "国外新药管线动态（ABI-4334 1b期），非中国证据"),
    ("CRKL", "科普/非专题（CRKL抑制剂联合抗PD-1治疗肝癌），非期刊来源"),
    ("AB-836", "国际会议报道（EASL2023 AB-836），非原始文献"),
    ("口服小分子HBV", "新药进展栏目（cccDNA抑制剂），非原始文献"),
    ("侯凤琴教授", "专家讲座（肝癌在线ICI肝损害），非期刊来源"),
    ("做个调查", "调查问卷（肝脏时间），非期刊来源"),
    ("质子泵抑制剂在慢加急性肝衰竭治疗中的应用", "特别关注栏目（ACLF），非专题"),
    ("PRI-724", "国外研究临床结果（EbioMedicine，非中国证据）"),
    ("AB-101", "国外研究（AB-101，非中国证据）"),
    ("免疫抗肿瘤时代不可回避的问题", "科普转载（ICIs肝损伤），非期刊来源"),
    ("特殊人群怎么办", "科普转载（ICIs特殊人群），非期刊来源"),
    ("谢青教授", "讲座转载（ICIs相关肝损伤诊治），非期刊来源"),
    ("GB1211", "国外新药管线动态（GB1211失代偿肝硬化2期），非中国证据"),
    ("GS-9688", "国外新药管线动态（GS-9688 2期），非中国证据"),
    ("ABI-4334首次人体", "国外新药管线动态（ABI-4334 FIH），非中国证据"),
    ("仑伐替尼", "非专题（晚期HCC仑伐替尼序贯治疗，非乙肝联合方案）"),
    ("ABI-H2158", "国外新药管线动态（ABI-H2158 1期），非中国证据"),
    ("RNaseH抑制剂", "国外研究报道（RNase H体外研究），非中国证据"),
    ("ZM-H1505R", "国外新药管线动态（ZM-H1505R Ⅰa期），非中国证据"),
    ("VNRX-9945", "国外新药管线动态（VNRX-9945），非中国证据"),
    ("黄祖雄教授", "专家讲座（肝癌在线ICIs肝损伤处理），非期刊来源"),
    ("NQO1抑制剂双香豆素", "与锁定条目同文转载（中华肝脏病杂志公众号），重复剔除（[13]已锁定J Hepatol原文）"),
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

    print(f"T4E 待核实条目: {len([r for r in data if r[0]==TOPIC and r[7]=='待核实'])}")
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
            print(f"  LOCK[{i}]: {ent[:44]} -> {lk[1] or lk[2]}")
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
