#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
广州盈骄恒贸易有限公司数据一致性对比分析
对比科目余额表（final_enhanced_balance.csv）和凭证明细（final_voucher_detail.csv）
"""

import pandas as pd
import numpy as np
from pathlib import Path
import datetime

# 设置文件路径
voucher_file = "/home/Fieons/Audit-p/format-data/financial/final_voucher_detail.csv"
balance_file = "/home/Fieons/Audit-p/format-data/financial/final_enhanced_balance.csv"
output_dir = "/home/Fieons/Audit-p/operation/output"

def load_and_preprocess_data():
    """加载并预处理数据"""
    print("正在读取数据文件...")
    
    try:
        # 读取凭证明细数据
        voucher_df = pd.read_csv(voucher_file)
        
        # 读取科目余额表数据
        balance_df = pd.read_csv(balance_file)
        
        # 数据预处理
        voucher_df['日期'] = pd.to_datetime(voucher_df['日期'], errors='coerce')
        voucher_df['月份'] = voucher_df['日期'].dt.month
        voucher_df['年份'] = voucher_df['日期'].dt.year
        
        # 清理金额字段中的逗号
        amount_columns = ['原币金额', '借方金额', '贷方金额']
        for col in amount_columns:
            if voucher_df[col].dtype == 'object':
                voucher_df[col] = voucher_df[col].str.replace(',', '').astype(float)
        
        return voucher_df, balance_df
        
    except Exception as e:
        print(f"读取数据时出错: {e}")
        return None, None

def extract_yingjiaoheng_data(voucher_df, balance_df):
    """提取盈骄恒相关数据"""
    
    # 从凭证明细中提取盈骄恒相关记录
    yjh_pattern = r'盈骄恒|盈娇恒|广州盈骄恒|佛山盈娇恒'
    yjh_vouchers = voucher_df[voucher_df['摘要'].str.contains(yjh_pattern, na=False, regex=True)]
    
    # 从科目余额表中提取盈骄恒相关记录
    yjh_balance = balance_df[balance_df['核算维度名称'].str.contains(yjh_pattern, na=False, regex=True)]
    
    # 特别关注其他应收款科目（1221.02）
    other_receivable_pattern = r'1221\.02'
    other_receivable_vouchers = yjh_vouchers[yjh_vouchers['科目编码'].str.contains(other_receivable_pattern, na=False, regex=True)]
    
    # 对于科目余额表，我们需要同时匹配科目编码和核算维度名称
    other_receivable_balance = balance_df[
        (balance_df['科目编码'].str.contains(other_receivable_pattern, na=False, regex=True)) &
        (balance_df['核算维度名称'].str.contains(yjh_pattern, na=False, regex=True))
    ]
    
    return {
        'yjh_vouchers': yjh_vouchers,
        'yjh_balance': yjh_balance,
        'other_receivable_vouchers': other_receivable_vouchers,
        'other_receivable_balance': other_receivable_balance
    }

def analyze_balance_consistency(yjh_data):
    """分析科目余额表的一致性"""
    
    balance_df = yjh_data['other_receivable_balance']
    vouchers_df = yjh_data['other_receivable_vouchers']
    
    print("\n=== 科目余额表一致性分析 ===")
    
    if balance_df.empty:
        print("未找到其他应收款科目（1221.02）中盈骄恒相关的余额记录")
        return None
    
    # 按公司和年份分组分析
    balance_summary = balance_df.groupby(['公司', '年份']).agg({
        '期初余额借方': 'sum',
        '期初余额贷方': 'sum',
        '本年累计借方': 'sum',
        '本年累计贷方': 'sum',
        '期末余额借方': 'sum',
        '期末余额贷方': 'sum'
    }).reset_index()
    
    for _, row in balance_summary.iterrows():
        print(f"\n{row['公司']} - {row['年份']}年:")
        print(f"  期初余额: 借 {row['期初余额借方']:.2f} | 贷 {row['期初余额贷方']:.2f}")
        print(f"  本年累计: 借 {row['本年累计借方']:.2f} | 贷 {row['本年累计贷方']:.2f}")
        print(f"  期末余额: 借 {row['期末余额借方']:.2f} | 贷 {row['期末余额贷方']:.2f}")
        
        # 检查余额计算是否正确
        calculated_end_debit = row['期初余额借方'] + row['本年累计借方'] - row['本年累计贷方']
        calculated_end_credit = row['期初余额贷方'] + row['本年累计贷方'] - row['本年累计借方']
        
        debit_diff = abs(row['期末余额借方'] - calculated_end_debit)
        credit_diff = abs(row['期末余额贷方'] - calculated_end_credit)
        
        if debit_diff > 0.01 or credit_diff > 0.01:
            print(f"  ⚠️  余额计算不一致!")
            print(f"  计算期末借: {calculated_end_debit:.2f}, 实际: {row['期末余额借方']:.2f}, 差异: {debit_diff:.2f}")
            print(f"  计算期末贷: {calculated_end_credit:.2f}, 实际: {row['期末余额贷方']:.2f}, 差异: {credit_diff:.2f}")
        else:
            print("  ✓ 余额计算正确")
    
    return balance_summary

def analyze_voucher_transactions(yjh_data):
    """分析凭证明细交易"""
    
    vouchers_df = yjh_data['other_receivable_vouchers']
    
    print("\n=== 凭证明细交易分析 ===")
    
    if vouchers_df.empty:
        print("未找到其他应收款科目（1221.02）中盈骄恒相关的凭证明细")
        return None
    
    # 按月份和公司分组
    monthly_summary = vouchers_df.groupby(['年份', '月份', '公司']).agg({
        '原币金额': 'sum',
        '借方金额': 'sum',
        '贷方金额': 'sum',
        '凭证号': 'count'
    }).reset_index()
    
    monthly_summary = monthly_summary.rename(columns={'凭证号': '交易笔数'})
    
    print(f"\n共找到 {len(vouchers_df)} 笔其他应收款相关交易")
    
    # 特别关注6月和11月的交易
    print("\n重点关注月份（6月、11月）交易情况:")
    focus_months = monthly_summary[monthly_summary['月份'].isin([6, 11])]
    
    for _, row in focus_months.iterrows():
        print(f"  {row['年份']}年{row['月份']}月 - {row['公司']}: {row['交易笔数']}笔交易, 总金额: {row['原币金额']:.2f}")
    
    # 详细交易记录
    print("\n详细交易记录:")
    for _, row in vouchers_df.iterrows():
        date_str = row['日期'].strftime('%Y-%m-%d') if pd.notna(row['日期']) else '未知日期'
        print(f"  {date_str} - {row['公司']} - {row['摘要']}: {row['原币金额']:.2f}")
    
    return monthly_summary

def compare_balance_vs_vouchers(balance_summary, voucher_summary, yjh_data):
    """对比科目余额表和凭证明细的一致性"""
    
    print("\n=== 数据一致性对比分析 ===")
    
    balance_df = yjh_data['other_receivable_balance']
    vouchers_df = yjh_data['other_receivable_vouchers']
    
    if balance_df.empty or vouchers_df.empty:
        print("缺少科目余额表或凭证明细数据，无法进行对比分析")
        return None
    
    # 按公司年份分组计算凭证明细的借贷总额
    voucher_totals = vouchers_df.groupby(['公司', '年份']).agg({
        '借方金额': 'sum',
        '贷方金额': 'sum'
    }).reset_index()
    
    # 合并科目余额表和凭证明细数据
    comparison = pd.merge(
        balance_summary[['公司', '年份', '本年累计借方', '本年累计贷方']],
        voucher_totals[['公司', '年份', '借方金额', '贷方金额']],
        on=['公司', '年份'],
        how='outer',
        suffixes=('_balance', '_voucher')
    )
    
    # 计算差异
    comparison['借方差异'] = comparison['本年累计借方'] - comparison['借方金额']
    comparison['贷方差异'] = comparison['本年累计贷方'] - comparison['贷方金额']
    
    print("\n科目余额表 vs 凭证明细对比:")
    for _, row in comparison.iterrows():
        print(f"\n{row['公司']} - {row['年份']}年:")
        print(f"  科目余额表 - 借: {row['本年累计借方']:.2f}, 贷: {row['本年累计贷方']:.2f}")
        print(f"  凭证明细   - 借: {row['借方金额']:.2f}, 贷: {row['贷方金额']:.2f}")
        print(f"  差异       - 借: {row['借方差异']:.2f}, 贷: {row['贷方差异']:.2f}")
        
        if abs(row['借方差异']) > 0.01 or abs(row['贷方差异']) > 0.01:
            print("  ⚠️  数据不一致!")
        else:
            print("  ✓ 数据一致")
    
    return comparison

def generate_detailed_report(yjh_data, balance_summary, voucher_summary, comparison_result):
    """生成详细分析报告"""
    
    report_content = """# 广州盈骄恒贸易有限公司数据一致性对比分析报告

## 分析概述
本报告对比分析了科目余额表（final_enhanced_balance.csv）和凭证明细（final_voucher_detail.csv）中
关于碳纤维公司、复合材料公司与广州盈骄恒贸易有限公司的往来数据一致性。

## 1. 数据概况
"""
    
    # 添加数据概况
    total_vouchers = len(yjh_data['yjh_vouchers'])
    total_balance_records = len(yjh_data['yjh_balance'])
    or_vouchers = len(yjh_data['other_receivable_vouchers'])
    or_balance_records = len(yjh_data['other_receivable_balance'])
    
    report_content += f"- 总盈骄恒相关凭证明细记录: {total_vouchers} 条\n"
    report_content += f"- 总盈骄恒相关科目余额记录: {total_balance_records} 条\n"
    report_content += f"- 其他应收款科目（1221.02）凭证明细: {or_vouchers} 条\n"
    report_content += f"- 其他应收款科目（1221.02）余额记录: {or_balance_records} 条\n\n"
    
    # 添加科目余额表分析
    report_content += "## 2. 科目余额表分析\n\n"
    if not balance_summary.empty:
        for _, row in balance_summary.iterrows():
            report_content += f"### {row['公司']} - {row['年份']}年\n"
            report_content += f"- 期初余额: 借方 {row['期初余额借方']:.2f}, 贷方 {row['期初余额贷方']:.2f}\n"
            report_content += f"- 本年累计: 借方 {row['本年累计借方']:.2f}, 贷方 {row['本年累计贷方']:.2f}\n"
            report_content += f"- 期末余额: 借方 {row['期末余额借方']:.2f}, 贷方 {row['期末余额贷方']:.2f}\n\n"
    else:
        report_content += "无相关科目余额记录\n\n"
    
    # 添加凭证明细分析
    report_content += "## 3. 凭证明细分析\n\n"
    if not voucher_summary.empty:
        for _, row in voucher_summary.iterrows():
            report_content += f"### {row['年份']}年{row['月份']}月 - {row['公司']}\n"
            report_content += f"- 交易笔数: {row['交易笔数']}\n"
            report_content += f"- 总金额: {row['原币金额']:.2f}\n"
            report_content += f"- 借方金额: {row['借方金额']:.2f}\n"
            report_content += f"- 贷方金额: {row['贷方金额']:.2f}\n\n"
    else:
        report_content += "无相关凭证明细记录\n\n"
    
    # 添加一致性对比
    report_content += "## 4. 数据一致性对比\n\n"
    if comparison_result is not None and not comparison_result.empty:
        for _, row in comparison_result.iterrows():
            report_content += f"### {row['公司']} - {row['年份']}年\n"
            report_content += f"- 科目余额表借贷: {row['本年累计借方']:.2f} / {row['本年累计贷方']:.2f}\n"
            report_content += f"- 凭证明细借贷: {row['借方金额']:.2f} / {row['贷方金额']:.2f}\n"
            report_content += f"- 差异: {row['借方差异']:.2f} / {row['贷方差异']:.2f}\n"
            
            if abs(row['借方差异']) > 0.01 or abs(row['贷方差异']) > 0.01:
                report_content += "- **状态: ❌ 不一致**\n\n"
            else:
                report_content += "- **状态: ✅ 一致**\n\n"
    else:
        report_content += "无法进行一致性对比\n\n"
    
    # 添加异常和发现
    report_content += "## 5. 异常和发现\n\n"
    
    # 检查6月和11月交易
    focus_vouchers = yjh_data['other_receivable_vouchers']
    if not focus_vouchers.empty:
        june_trans = focus_vouchers[focus_vouchers['月份'] == 6]
        nov_trans = focus_vouchers[focus_vouchers['月份'] == 11]
        
        report_content += f"### 6月交易情况\n"
        if not june_trans.empty:
            for _, row in june_trans.iterrows():
                date_str = row['日期'].strftime('%Y-%m-%d') if pd.notna(row['日期']) else '未知日期'
                report_content += f"- {date_str}: {row['摘要']} - {row['原币金额']:.2f}\n"
        else:
            report_content += "- 无6月交易记录\n"
        
        report_content += f"\n### 11月交易情况\n"
        if not nov_trans.empty:
            for _, row in nov_trans.iterrows():
                date_str = row['日期'].strftime('%Y-%m-%d') if pd.notna(row['日期']) else '未知日期'
                report_content += f"- {date_str}: {row['摘要']} - {row['原币金额']:.2f}\n"
        else:
            report_content += "- 无11月交易记录\n"
    
    # 添加建议
    report_content += "\n## 6. 建议和进一步调查事项\n\n"
    report_content += "1. 对于数据不一致的情况，建议核对原始凭证和账簿记录\n"
    report_content += "2. 检查是否有未录入系统的交易或调整分录\n"
    report_content += "3. 验证科目余额表的计算公式是否正确\n"
    report_content += "4. 确认所有盈骄恒相关交易都已正确分类到其他应收款科目\n"
    report_content += "5. 检查是否有跨期调整或重分类事项\n"
    
    # 保存报告
    report_path = f"{output_dir}/yingjiaoheng_consistency_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"\n详细分析报告已保存至: {report_path}")
    
    return report_path

def main():
    """主函数"""
    print("开始广州盈骄恒贸易有限公司数据一致性对比分析...")
    
    # 加载数据
    voucher_df, balance_df = load_and_preprocess_data()
    if voucher_df is None or balance_df is None:
        return
    
    # 提取盈骄恒相关数据
    yjh_data = extract_yingjiaoheng_data(voucher_df, balance_df)
    
    # 分析科目余额表一致性
    balance_summary = analyze_balance_consistency(yjh_data)
    
    # 分析凭证明细交易
    voucher_summary = analyze_voucher_transactions(yjh_data)
    
    # 对比数据一致性
    comparison_result = compare_balance_vs_vouchers(balance_summary, voucher_summary, yjh_data)
    
    # 生成详细报告
    report_path = generate_detailed_report(yjh_data, balance_summary, voucher_summary, comparison_result)
    
    print(f"\n分析完成! 详细报告请查看: {report_path}")

if __name__ == "__main__":
    main()