#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终分析：广州盈骄恒和佛山盈娇恒还给碳纤维和复合材料公司的款项数据
"""

import pandas as pd
import numpy as np

# 设置文件路径
voucher_file = "/home/Fieons/Audit-p/format-data/financial/final_voucher_detail.csv"
balance_file = "/home/Fieons/Audit-p/format-data/financial/final_enhanced_balance.csv"

def analyze_repayment_data():
    """分析还款数据"""
    
    print("正在分析广州盈骄恒和佛山盈娇恒还款数据...")
    
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
        
        # 读取科目余额表数据
        balance_df = pd.read_csv(balance_file)
        
        # 筛选盈骄恒/盈娇恒相关的余额记录
        yjh_balance = balance_df[balance_df['核算维度名称'].str.contains(yjh_pattern, na=False, regex=True)]
        
        # 筛选2023和2024年的余额数据
        yjh_balance_2023_2024 = yjh_balance[yjh_balance['年份'].isin([2023, 2024])]
        
        print("=" * 80)
        print("广州盈骄恒和佛山盈娇恒还给碳纤维和复合材料公司的款项分析")
        print("=" * 80)
        
        # 分析凭证明细中的还款数据
        if not repayment_df.empty:
            print("\n1. 凭证明细中的还款记录:")
            print("-" * 50)
            
            # 按年份和公司统计总额
            yearly_company_total = repayment_df.groupby(['年份', '公司']).agg({
                '借方金额': 'sum'
            }).reset_index()
            
            for _, row in yearly_company_total.iterrows():
                print(f"{int(row['年份'])}年 - {row['公司']}: {row['借方金额']:,.2f}元")
            
            # 按年份统计总额
            yearly_total = repayment_df.groupby('年份').agg({
                '借方金额': 'sum'
            }).reset_index()
            
            print("\n年度还款总额:")
            for _, row in yearly_total.iterrows():
                print(f"{int(row['年份'])}年还款总额: {row['借方金额']:,.2f}元")
                
            # 计算总还款金额
            total_repayment = yearly_total['借方金额'].sum()
            print(f"\n2023-2024年总还款金额: {total_repayment:,.2f}元")
            
        else:
            print("\n1. 凭证明细中未找到2023-2024年的还款记录")
        
        # 分析科目余额表中的相关数据
        print("\n2. 科目余额表中的相关数据:")
        print("-" * 50)
        
        if not yjh_balance_2023_2024.empty:
            # 按年份和公司分组
            for year in [2023, 2024]:
                year_data = yjh_balance_2023_2024[yjh_balance_2023_2024['年份'] == year]
                if not year_data.empty:
                    print(f"\n{year}年余额情况:")
                    
                    # 按公司分组
                    companies = year_data['核算维度名称'].unique()
                    for company in companies:
                        company_data = year_data[year_data['核算维度名称'] == company]
                        total_debit = company_data['本年累计借方'].sum()
                        total_credit = company_data['本年累计贷方'].sum()
                        
                        if total_debit > 0 or total_credit > 0:
                            print(f"  {company}: 本年累计借方 {total_debit:,.2f}元, 本年累计贷方 {total_credit:,.2f}元")
        
        # 最终统计结果
        print("\n3. 最终统计结果:")
        print("-" * 50)
        
        if not repayment_df.empty:
            # 2024年还款详情
            repayment_2024 = repayment_df[repayment_df['年份'] == 2024]
            if not repayment_2024.empty:
                total_2024 = repayment_2024['借方金额'].sum()
                print(f"2024年实际还款总额: {total_2024:,.2f}元")
                
                # 按公司细分
                for company in repayment_2024['公司'].unique():
                    company_data = repayment_2024[repayment_2024['公司'] == company]
                    company_total = company_data['借方金额'].sum()
                    print(f"  - {company}: {company_total:,.2f}元")
        
        # 2023年情况说明
        print(f"\n2023年情况: 凭证明细数据中无2023年记录，但从科目余额表可见相关业务往来")
        
        print("\n" + "=" * 80)
        
        return repayment_df
        
    except Exception as e:
        print(f"分析数据时出错: {e}")
        return None

if __name__ == "__main__":
    analyze_repayment_data()