#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询广州盈骄恒和佛山盈娇恒2023-2024年还款记录
"""

import pandas as pd
import numpy as np
from pathlib import Path

# 设置文件路径
voucher_file = "/home/Fieons/Audit-p/format-data/financial/final_voucher_detail.csv"
balance_file = "/home/Fieons/Audit-p/format-data/financial/final_enhanced_balance.csv"

def query_yingjiaoheng_repayment():
    """查询盈骄恒/盈娇恒还款记录"""
    
    print("正在读取数据文件...")
    
    try:
        # 读取凭证明细数据
        voucher_df = pd.read_csv(voucher_file)
        
        # 筛选盈骄恒/盈娇恒相关的记录
        yjh_pattern = r'盈骄恒|盈娇恒'
        yjh_df = voucher_df[voucher_df['摘要'].str.contains(yjh_pattern, na=False, regex=True)]
        
        # 筛选还款相关的记录
        repayment_keywords = ['还款', '付款', '支付', '付', '还', '收.*款']
        repayment_pattern = '|'.join(repayment_keywords)
        repayment_df = yjh_df[yjh_df['摘要'].str.contains(repayment_pattern, na=False, regex=True)]
        
        # 提取年份信息
        repayment_df['年份'] = pd.to_datetime(repayment_df['日期']).dt.year
        
        # 筛选2023和2024年的数据
        repayment_2023_2024 = repayment_df[repayment_df['年份'].isin([2023, 2024])]
        
        # 按年份和公司分组统计
        if not repayment_2023_2024.empty:
            print("\n=== 广州盈骄恒和佛山盈娇恒2023-2024年还款记录 ===")
            
            # 按年份和摘要分组统计
            yearly_summary = repayment_2023_2024.groupby(['年份', '摘要']).agg({
                '原币金额': 'sum',
                '借方金额': 'sum', 
                '贷方金额': 'sum'
            }).reset_index()
            
            # 按年份统计总额
            yearly_total = repayment_2023_2024.groupby('年份').agg({
                '原币金额': 'sum',
                '借方金额': 'sum',
                '贷方金额': 'sum'
            }).reset_index()
            
            print("\n详细还款记录:")
            for _, row in yearly_summary.iterrows():
                print(f"{row['年份']}年 - {row['摘要']}: {row['原币金额']:.2f}元")
            
            print("\n年度还款总额:")
            for _, row in yearly_total.iterrows():
                print(f"{row['年份']}年还款总额: {row['原币金额']:.2f}元")
                
            # 计算总还款金额
            total_repayment = yearly_total['原币金额'].sum()
            print(f"\n2023-2024年总还款金额: {total_repayment:.2f}元")
            
            # 显示所有相关记录
            print(f"\n共找到 {len(repayment_2023_2024)} 条相关记录")
            
            return repayment_2023_2024
            
        else:
            print("未找到2023-2024年广州盈骄恒和佛山盈娇恒的还款记录")
            
            # 检查所有相关记录
            print("\n所有盈骄恒/盈娇恒相关记录:")
            for _, row in yjh_df.iterrows():
                print(f"{row['日期']} - {row['摘要']}: {row['原币金额']:.2f}元")
            
            return None
            
    except Exception as e:
        print(f"读取数据时出错: {e}")
        return None

def analyze_balance_data():
    """分析科目余额表中的相关数据"""
    
    try:
        # 读取科目余额表数据
        balance_df = pd.read_csv(balance_file)
        
        # 筛选盈骄恒/盈娇恒相关的记录
        yjh_pattern = r'盈骄恒|盈娇恒'
        yjh_balance = balance_df[balance_df['核算维度名称'].str.contains(yjh_pattern, na=False, regex=True)]
        
        # 筛选2023和2024年的数据
        yjh_balance_2023_2024 = yjh_balance[yjh_balance['年份'].isin([2023, 2024])]
        
        if not yjh_balance_2023_2024.empty:
            print("\n=== 科目余额表中的相关数据 ===")
            
            # 按年份和科目分组
            balance_summary = yjh_balance_2023_2024.groupby(['年份', '科目名称', '核算维度名称']).agg({
                '期初余额借方': 'sum',
                '期初余额贷方': 'sum',
                '本年累计借方': 'sum',
                '本年累计贷方': 'sum',
                '期末余额借方': 'sum',
                '期末余额贷方': 'sum'
            }).reset_index()
            
            for _, row in balance_summary.iterrows():
                print(f"{row['年份']}年 - {row['核算维度名称']} - {row['科目名称']}:")
                print(f"  期初借: {row['期初余额借方']:.2f}, 期初贷: {row['期初余额贷方']:.2f}")
                print(f"  本年借: {row['本年累计借方']:.2f}, 本年贷: {row['本年累计贷方']:.2f}")
                print(f"  期末借: {row['期末余额借方']:.2f}, 期末贷: {row['期末余额贷方']:.2f}")
        
        return yjh_balance_2023_2024
        
    except Exception as e:
        print(f"分析科目余额表时出错: {e}")
        return None

if __name__ == "__main__":
    print("开始查询广州盈骄恒和佛山盈娇恒还款记录...")
    
    # 查询凭证明细中的还款记录
    repayment_data = query_yingjiaoheng_repayment()
    
    # 分析科目余额表中的相关数据
    balance_data = analyze_balance_data()
    
    print("\n查询完成!")