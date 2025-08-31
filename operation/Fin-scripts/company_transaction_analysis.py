#!/usr/bin/env python3
"""
公司交易详细分析报告
分析广州盈骄恒贸易有限公司、佛山市盈娇恒新材料有限公司的交易情况
并与科目余额表进行对比分析
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def analyze_company_transactions():
    """分析公司交易并与科目余额表对比"""
    
    # 文件路径
    voucher_file = "/home/Fieons/Audit-p/format-data/financial/final_voucher_detail.csv"
    balance_file = "/home/Fieons/Audit-p/format-data/financial/final_enhanced_balance.csv"
    output_file = "/home/Fieons/Audit-p/operation/output/company_detailed_analysis.csv"
    report_file = "/home/Fieons/Audit-p/operation/output/company_analysis_report.txt"
    
    print("开始分析公司交易数据...")
    
    try:
        # 读取凭证明细数据
        voucher_df = pd.read_csv(voucher_file)
        print(f"凭证明细记录总数：{len(voucher_df)}")
        
        # 读取科目余额表数据
        balance_df = pd.read_csv(balance_file)
        print(f"科目余额表记录数：{len(balance_df)}")
        
        # 目标公司名称
        target_companies = [
            "广州盈骄恒贸易有限公司",
            "佛山市盈娇恒新材料有限公司"
        ]
        
        # 在凭证明细中查找相关记录
        company_filter = voucher_df['摘要'].str.contains('|'.join(target_companies), na=False, case=False)
        subject_filter = voucher_df['科目全名'].str.contains('|'.join(target_companies), na=False, case=False)
        combined_filter = company_filter | subject_filter
        
        company_vouchers = voucher_df[combined_filter].copy()
        
        if len(company_vouchers) == 0:
            print("未找到相关凭证明细记录")
            return
        
        print(f"找到相关凭证明细记录：{len(company_vouchers)} 条")
        
        # 添加分析字段
        def identify_company(row):
            text = str(row['摘要']) + " " + str(row['科目全名'])
            if "广州盈骄恒贸易有限公司" in text:
                return "广州盈骄恒贸易有限公司"
            elif "佛山市盈娇恒新材料有限公司" in text:
                return "佛山市盈娇恒新材料有限公司"
            else:
                return "其他相关公司"
        
        company_vouchers['匹配公司'] = company_vouchers.apply(identify_company, axis=1)
        
        # 提取对方单位
        def extract_counterpart(summary):
            if pd.isna(summary):
                return ""
            if "/" in summary:
                parts = summary.split("/")
                if len(parts) > 1:
                    return parts[1].strip()
            return ""
        
        company_vouchers['对方单位'] = company_vouchers['摘要'].apply(extract_counterpart)
        
        # 识别业务类型
        def identify_business_type(summary):
            if pd.isna(summary):
                return "未知"
            summary_lower = summary.lower()
            if any(keyword in summary_lower for keyword in ["废料", "处置", "回收"]):
                return "废料处置"
            elif any(keyword in summary_lower for keyword in ["采购", "购买", "材料"]):
                return "材料采购"
            elif any(keyword in summary_lower for keyword in ["销售", "货款", "收款"]):
                return "销售收款"
            elif any(keyword in summary_lower for keyword in ["付款", "支付"]):
                return "付款业务"
            else:
                return "其他业务"
        
        company_vouchers['业务类型'] = company_vouchers['摘要'].apply(identify_business_type)
        
        # 创建详细分析表
        analysis_columns = [
            '日期', '凭证字', '凭证号', '摘要', '科目编码', '科目全名',
            '借方金额', '贷方金额', '原币金额', '币别',
            '匹配公司', '对方单位', '业务类型',
            '会计年度', '期间', '制单', '审核', '公司', '凭证唯一标识'
        ]
        
        available_columns = [col for col in analysis_columns if col in company_vouchers.columns]
        detailed_analysis = company_vouchers[available_columns].copy()
        
        # 按日期和凭证号排序
        detailed_analysis = detailed_analysis.sort_values(['日期', '凭证字', '凭证号'])
        
        # 保存详细分析结果
        detailed_analysis.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"详细分析结果已保存到：{output_file}")
        
        # 生成分析报告
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=== 公司交易详细分析报告 ===\n\n")
            f.write(f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"数据来源：{voucher_file}\n")
            f.write(f"分析目标：{', '.join(target_companies)}\n\n")
            
            f.write("=== 交易概览 ===\n")
            f.write(f"总交易记录数：{len(detailed_analysis)}\n")
            f.write(f"涉及凭证数：{detailed_analysis['凭证唯一标识'].nunique()}\n")
            f.write(f"时间范围：{detailed_analysis['日期'].min()} 至 {detailed_analysis['日期'].max()}\n\n")
            
            f.write("=== 按公司统计 ===\n")
            company_stats = detailed_analysis['匹配公司'].value_counts()
            for company, count in company_stats.items():
                f.write(f"{company}: {count} 条记录\n")
            f.write("\n")
            
            f.write("=== 按业务类型统计 ===\n")
            business_stats = detailed_analysis['业务类型'].value_counts()
            for business, count in business_stats.items():
                f.write(f"{business}: {count} 条记录\n")
            f.write("\n")
            
            f.write("=== 金额统计 ===\n")
            total_debit = detailed_analysis['借方金额'].fillna(0).sum()
            total_credit = detailed_analysis['贷方金额'].fillna(0).sum()
            f.write(f"借方金额合计：{total_debit:,.2f} 元\n")
            f.write(f"贷方金额合计：{total_credit:,.2f} 元\n")
            f.write(f"净额：{total_debit - total_credit:,.2f} 元\n\n")
            
            f.write("=== 交易明细摘要 ===\n")
            for idx, row in detailed_analysis.iterrows():
                f.write(f"{row['日期']} | {row['凭证字']}-{row['凭证号']} | {row['摘要']} | ")
                f.write(f"借方：{row['借方金额'] if pd.notna(row['借方金额']) else 0:,.2f} | ")
                f.write(f"贷方：{row['贷方金额'] if pd.notna(row['贷方金额']) else 0:,.2f} | ")
                f.write(f"{row['业务类型']}\n")
            
            f.write("\n=== 与科目余额表对比分析 ===\n")
            
            # 查找相关科目余额
            related_subjects = detailed_analysis['科目编码'].unique()
            subject_balances = balance_df[balance_df['科目编码'].isin(related_subjects)]
            
            if len(subject_balances) > 0:
                f.write(f"找到 {len(subject_balances)} 个相关科目的余额信息\n")
                for _, balance_row in subject_balances.iterrows():
                    subject_code = balance_row['科目编码']
                    subject_name = balance_row['科目名称']
                    period = balance_row['期间']
                    debit_balance = balance_row['期末余额借方']
                    credit_balance = balance_row['期末余额贷方']
                    
                    f.write(f"科目 {subject_code} ({subject_name}) - 期间 {period}: ")
                    f.write(f"期末借方余额：{debit_balance if pd.notna(debit_balance) else 0:,.2f}, ")
                    f.write(f"期末贷方余额：{credit_balance if pd.notna(credit_balance) else 0:,.2f}\n")
            else:
                f.write("未找到相关科目的余额信息\n")
            
            f.write("\n=== 风险提示 ===\n")
            f.write("1. 注意检查废料处置业务的合规性和定价合理性\n")
            f.write("2. 关注其他应收款科目的余额变化情况\n")
            f.write("3. 建议进一步核实交易的真实性和完整性\n")
            f.write("4. 检查是否存在关联方交易未充分披露的情况\n")
        
        print(f"分析报告已保存到：{report_file}")
        
        # 打印关键统计信息
        print("\n=== 分析结果摘要 ===")
        print(f"涉及公司：{', '.join(company_stats.index.tolist())}")
        print(f"业务类型：{', '.join(business_stats.index.tolist())}")
        print(f"总交易金额：{total_debit + total_credit:,.2f} 元")
        print(f"净影响金额：{total_debit - total_credit:,.2f} 元")
        
        return detailed_analysis
        
    except Exception as e:
        print(f"分析过程中出现错误：{e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

if __name__ == "__main__":
    analyze_company_transactions()