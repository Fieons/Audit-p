#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd

# 读取汇总数据
df = pd.read_csv('/home/Fieons/Audit-p/format-data/financial/yingjiaoheng_balance_summary.csv')

# 创建详细分析报告
analysis_report = []

# 1. 按公司和科目类型分析
print("=== 盈骄恒往来科目余额分析报告 ===\n")

# 碳纤维公司分析
txw_data = df[df['公司名称'] == '广州金发碳纤维新材料发展有限公司']
print("1. 碳纤维公司（广州金发碳纤维新材料发展有限公司）盈骄恒往来情况：")

for year in sorted(txw_data['年份'].unique()):
    year_data = txw_data[txw_data['年份'] == year]
    print(f"\n   {year}年:")
    
    for _, row in year_data.iterrows():
        direction_symbol = "借" if row['期末余额方向'] == '借' else "贷"
        print(f"     {row['科目名称']}({row['科目编码']}): {row['期末余额']:,.2f} {direction_symbol}")

# 复合材料公司分析
fh_data = df[df['公司名称'] == '广东金发复合材料有限公司']
print("\n2. 复合材料公司（广东金发复合材料有限公司）盈骄恒往来情况：")

for year in sorted(fh_data['年份'].unique()):
    year_data = fh_data[fh_data['年份'] == year]
    print(f"\n   {year}年:")
    
    for _, row in year_data.iterrows():
        direction_symbol = "借" if row['期末余额方向'] == '借' else "贷"
        print(f"     {row['科目名称']}({row['科目编码']}): {row['期末余额']:,.2f} {direction_symbol}")

# 3. 余额变化趋势分析
print("\n3. 余额变化趋势分析：")

# 碳纤维公司其他应收款变化
txw_receivable = txw_data[txw_data['科目编码'] == '1221.02']
print("\n   碳纤维公司其他应收款(供应商往来)变化:")
for _, row in txw_receivable.sort_values('年份').iterrows():
    print(f"     {row['年份']}年: {row['期末余额']:,.2f} {row['期末余额方向']}")

# 应付账款变化分析
payable_data = df[df['科目编码'].astype(str).str.contains('2202')]
print("\n   应付账款变化:")
for company in payable_data['公司名称'].unique():
    company_data = payable_data[payable_data['公司名称'] == company]
    print(f"\n   {company}:")
    for year in sorted(company_data['年份'].unique()):
        year_data = company_data[company_data['年份'] == year]
        total_payable = year_data['期末余额'].sum()
        print(f"     {year}年应付账款总额: {total_payable:,.2f} 贷")

# 4. 生成详细统计表
detailed_stats = df.groupby(['公司名称', '年份', '科目名称']).agg({
    '期初余额': 'first',
    '期初余额方向': 'first',
    '期末余额': 'first',
    '期末余额方向': 'first'
}).reset_index()

# 保存详细统计表
detailed_output_path = '/home/Fieons/Audit-p/format-data/financial/yingjiaoheng_detailed_analysis.csv'
detailed_stats.to_csv(detailed_output_path, index=False, encoding='utf-8-sig')

print(f"\n详细分析报告已保存到: {detailed_output_path}")

# 显示关键发现
print("\n=== 关键发现 ===")
print("1. 碳纤维公司对盈骄恒存在大额其他应收款（供应商往来）")
print("2. 2023-2024年期间，其他应收款从贷方122,222.40元变为借方2,675,590.60元")
print("3. 2024-2025年期间，其他应收款保持在1,875,590.60元借方余额")
print("4. 复合材料公司主要涉及应付账款（暂估应付款），金额相对较小")
print("5. 两家公司都存在与盈骄恒的持续业务往来")