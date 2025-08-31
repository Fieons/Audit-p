#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询广州盈骄恒和佛山盈娇恒还给碳纤维和复合材料公司的款项数据
"""

import pandas as pd
import numpy as np
from pathlib import Path

# 设置文件路径
voucher_file = "/home/Fieons/Audit-p/format-data/financial/final_voucher_detail.csv"

def query_carbon_composite_repayment():
    """查询盈骄恒/盈娇恒还给碳纤维和复合材料公司的款项"""
    
    print("正在读取凭证明细数据...")
    
    try:
        # 读取凭证明细数据
        voucher_df = pd.read_csv(voucher_file)
        
        # 筛选盈骄恒/盈娇恒相关的记录
        yjh_pattern = r'盈骄恒|盈娇恒'
        yjh_df = voucher_df[voucher_df['摘要'].str.contains(yjh_pattern, na=False, regex=True)]
        
        # 筛选收款方为碳纤维和复合材料公司的记录
        carbon_pattern = r'碳纤维|复合材料'
        carbon_companies = ['广州金发碳纤维新材料发展有限公司', '广东金发复合材料有限公司']
        
        # 筛选公司为碳纤维或复合材料公司的记录
        carbon_df = yjh_df[yjh_df['公司'].isin(carbon_companies)]
        
        # 提取年份信息
        carbon_df['年份'] = pd.to_datetime(carbon_df['日期']).dt.year
        
        # 筛选2023和2024年的数据
        carbon_2023_2024 = carbon_df[carbon_df['年份'].isin([2023, 2024])]
        
        # 筛选还款相关的记录（借方金额为正数，表示收到款项）
        repayment_df = carbon_2023_2024[carbon_2023_2024['借方金额'] > 0]
        
        if not repayment_df.empty:
            print("\n=== 广州盈骄恒和佛山盈娇恒还给碳纤维和复合材料公司的款项 ===")
            
            # 按年份、公司和摘要分组统计
            summary = repayment_df.groupby(['年份', '公司', '摘要']).agg({
                '借方金额': 'sum',
                '原币金额': 'sum'
            }).reset_index()
            
            # 按年份和公司统计总额
            yearly_company_total = repayment_df.groupby(['年份', '公司']).agg({
                '借方金额': 'sum',
                '原币金额': 'sum'
            }).reset_index()
            
            # 按年份统计总额
            yearly_total = repayment_df.groupby('年份').agg({
                '借方金额': 'sum',
                '原币金额': 'sum'
            }).reset_index()
            
            print("\n详细还款记录:")
            for _, row in summary.iterrows():
                print(f"{row['年份']}年 - {row['公司']} - {row['摘要']}: {row['借方金额']:.2f}元")
            
            print("\n按公司和年份统计:")
            for _, row in yearly_company_total.iterrows():
                print(f"{row['年份']}年 - {row['公司']}: {row['借方金额']:.2f}元")
            
            print("\n年度还款总额:")
            for _, row in yearly_total.iterrows():
                print(f"{row['年份']}年还款总额: {row['借方金额']:.2f}元")
                
            # 计算总还款金额
            total_repayment = yearly_total['借方金额'].sum()
            print(f"\n2023-2024年总还款金额: {total_repayment:.2f}元")
            
            # 显示所有相关记录
            print(f"\n共找到 {len(repayment_df)} 条相关记录")
            
            return repayment_df
            
        else:
            print("未找到2023-2024年广州盈骄恒和佛山盈娇恒还给碳纤维和复合材料公司的还款记录")
            
            # 检查所有相关记录
            print("\n所有盈骄恒/盈娇恒相关记录:")
            for _, row in carbon_df.iterrows():
                print(f"{row['日期']} - {row['公司']} - {row['摘要']}: 借{row['借方金额']:.2f}元, 贷{row['贷方金额']:.2f}元")
            
            return None
            
    except Exception as e:
        print(f"读取数据时出错: {e}")
        return None

def get_detailed_repayment_data():
    """获取详细的还款数据"""
    
    try:
        # 读取凭证明细数据
        voucher_df = pd.read_csv(voucher_file)
        
        # 筛选盈骄恒/盈娇恒相关的记录
        yjh_pattern = r'盈骄恒|盈娇恒'
        yjh_df = voucher_df[voucher_df['摘要'].str.contains(yjh_pattern, na=False, regex=True)]
        
        # 筛选收款方为碳纤维和复合材料公司的记录
        carbon_companies = ['广州金发碳纤维新材料发展有限公司', '广东金发复合材料有限公司']
        carbon_df = yjh_df[yjh_df['公司'].isin(carbon_companies)]
        
        # 提取年份信息
        carbon_df['年份'] = pd.to_datetime(carbon_df['日期']).dt.year
        
        # 筛选2023和2024年的数据
        carbon_2023_2024 = carbon_df[carbon_df['年份'].isin([2023, 2024])]
        
        # 筛选还款相关的记录（借方金额为正数，表示收到款项）
        repayment_df = carbon_2023_2024[carbon_2023_2024['借方金额'] > 0]
        
        return repayment_df
        
    except Exception as e:
        print(f"获取详细数据时出错: {e}")
        return None

if __name__ == "__main__":
    print("开始查询广州盈骄恒和佛山盈娇恒还给碳纤维和复合材料公司的款项...")
    
    # 查询还款记录
    repayment_data = query_carbon_composite_repayment()
    
    print("\n查询完成!")