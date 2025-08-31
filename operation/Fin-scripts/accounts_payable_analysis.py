#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析广州盈骄恒和佛山盈娇恒的应付账款情况
"""

import pandas as pd

# 设置文件路径
balance_file = "/home/Fieons/Audit-p/format-data/financial/final_enhanced_balance.csv"

def analyze_accounts_payable():
    """分析应付账款情况"""
    
    print("正在读取科目余额表数据...")
    
    try:
        # 读取科目余额表数据
        balance_df = pd.read_csv(balance_file)
        
        # 筛选盈骄恒/盈娇恒相关的应付账款记录
        yjh_pattern = r'盈骄恒|盈娇恒'
        yjh_payable = balance_df[(balance_df['核算维度名称'].str.contains(yjh_pattern, na=False, regex=True)) &
                               (balance_df['科目编码'].str.startswith('2202', na=False))]
        
        # 筛选2023和2024年的数据
        yjh_payable_2023_2024 = yjh_payable[yjh_payable['年份'].isin([2023, 2024])]
        
        if not yjh_payable_2023_2024.empty:
            print("\n=== 广州盈骄恒和佛山盈娇恒应付账款情况 ===")
            
            for _, row in yjh_payable_2023_2024.iterrows():
                company = row['核算维度名称']
                year = int(row['年份'])
                subject = row['科目名称']
                
                print(f"\n{year}年 - {company} - {subject}:")
                print(f"  期初贷方余额: {row['期初余额贷方']:.2f}元")
                print(f"  本年借方发生额: {row['本年累计借方']:.2f}元 (付款/还款)")
                print(f"  本年贷方发生额: {row['本年累计贷方']:.2f}元 (新增应付)")
                print(f"  期末贷方余额: {row['期末余额贷方']:.2f}元")
                
                # 计算净变化
                net_change = row['本年累计贷方'] - row['本年累计借方']
                print(f"  净变化: {net_change:.2f}元")
                
        else:
            print("未找到2023-2024年广州盈骄恒和佛山盈娇恒的应付账款记录")
            
    except Exception as e:
        print(f"分析应付账款时出错: {e}")

def check_all_related_accounts():
    """检查所有相关科目"""
    
    try:
        balance_df = pd.read_csv(balance_file)
        
        # 筛选盈骄恒/盈娇恒相关的所有记录
        yjh_pattern = r'盈骄恒|盈娇恒'
        yjh_all = balance_df[balance_df['核算维度名称'].str.contains(yjh_pattern, na=False, regex=True)]
        
        # 筛选2023和2024年的数据
        yjh_all_2023_2024 = yjh_all[yjh_all['年份'].isin([2023, 2024])]
        
        if not yjh_all_2023_2024.empty:
            print("\n=== 所有相关科目余额 ===")
            
            for _, row in yjh_all_2023_2024.iterrows():
                company = row['核算维度名称']
                year = int(row['年份'])
                subject = row['科目名称']
                subject_code = row['科目编码']
                
                print(f"\n{year}年 - {company} - {subject} ({subject_code}):")
                print(f"  期初借: {row['期初余额借方']:.2f}, 期初贷: {row['期初余额贷方']:.2f}")
                print(f"  本年借: {row['本年累计借方']:.2f}, 本年贷: {row['本年累计贷方']:.2f}")
                print(f"  期末借: {row['期末余额借方']:.2f}, 期末贷: {row['期末余额贷方']:.2f}")
                
        else:
            print("未找到2023-2024年广州盈骄恒和佛山盈娇恒的任何科目记录")
            
    except Exception as e:
        print(f"检查所有科目时出错: {e}")

if __name__ == "__main__":
    print("开始分析广州盈骄恒和佛山盈娇恒的应付账款情况...")
    
    # 分析应付账款
    analyze_accounts_payable()
    
    # 检查所有相关科目
    check_all_related_accounts()
    
    print("\n分析完成!")