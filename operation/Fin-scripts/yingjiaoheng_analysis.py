#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import os

# 读取科目余额表数据
df = pd.read_csv('/home/Fieons/Audit-p/format-data/financial/final_enhanced_balance.csv')

# 筛选与盈骄恒相关的数据
yingjiaoheng_data = df[df['核算维度名称'] == '广州盈骄恒贸易有限公司']

# 筛选碳纤维公司和复合材料公司
target_companies = ['广州金发碳纤维新材料发展有限公司', '广东金发复合材料有限公司']
filtered_data = yingjiaoheng_data[yingjiaoheng_data['公司'].isin(target_companies)]

# 定义往来科目编码范围
receivable_codes = ['1221', '1221.02']  # 其他应收款/供应商往来
payable_codes = ['2202', '2202.01', '2202.06']  # 应付账款相关

# 进一步筛选往来科目
related_data = filtered_data[
    filtered_data['subject_code_path'].str.contains('|'.join(receivable_codes + payable_codes))
]

# 计算期初余额和期末余额
def calculate_balance(row):
    """根据借贷方向计算期初余额和期末余额"""
    # 期初余额
    if row['期初余额借方'] > 0:
        begin_balance = row['期初余额借方']
        begin_direction = '借'
    else:
        begin_balance = row['期初余额贷方']
        begin_direction = '贷'
    
    # 期末余额
    if row['期末余额借方'] > 0:
        end_balance = row['期末余额借方']
        end_direction = '借'
    else:
        end_balance = row['期末余额贷方']
        end_direction = '贷'
    
    return begin_balance, begin_direction, end_balance, end_direction

# 应用计算函数
results = []
for _, row in related_data.iterrows():
    begin_balance, begin_direction, end_balance, end_direction = calculate_balance(row)
    
    results.append({
        '公司名称': row['公司'],
        '科目编码': row['subject_code_path'].split('/')[-2] if row['subject_code_path'].split('/')[-2] != '' else row['subject_code_path'].split('/')[-3],
        '科目名称': row['subject_name_path'].split('/')[-2] if row['subject_name_path'].split('/')[-2] != '' else row['subject_name_path'].split('/')[-3],
        '年份': row['年份'],
        '期初余额': begin_balance,
        '期初余额方向': begin_direction,
        '期末余额': end_balance,
        '期末余额方向': end_direction,
        '核算维度': row['核算维度名称']
    })

# 创建结果DataFrame
result_df = pd.DataFrame(results)

# 保存结果到CSV文件
output_path = '/home/Fieons/Audit-p/format-data/financial/yingjiaoheng_balance_summary.csv'
result_df.to_csv(output_path, index=False, encoding='utf-8-sig')

print(f"分析完成！结果已保存到: {output_path}")
print(f"共找到 {len(result_df)} 条相关记录")
print("\n汇总表预览:")
print(result_df.head())

# 按公司和年份分组统计
print("\n按公司和年份的分组统计:")
grouped_stats = result_df.groupby(['公司名称', '年份']).agg({
    '期初余额': 'sum',
    '期末余额': 'sum',
    '科目名称': 'count'
}).rename(columns={'科目名称': '科目数量'})
print(grouped_stats)