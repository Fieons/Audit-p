#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np

def analyze_yingjiaheng_transactions():
    """详细分析盈骄恒公司的交易数据"""
    
    # 读取数据
    voucher_file = "/home/Fieons/Audit-p/format-data/financial/final_voucher_detail.csv"
    df_voucher = pd.read_csv(voucher_file)
    
    # 筛选盈骄恒相关交易
    yingjiaheng_mask = df_voucher['摘要'].str.contains('盈骄恒|盈娇恒', na=False)
    yingjiaheng_df = df_voucher[yingjiaheng_mask].copy()
    
    print("=== 盈骄恒公司交易详细分析 ===\n")
    
    # 按公司分类
    print("1. 交易按文件来源分类:")
    file_counts = yingjiaheng_df['文件来源'].value_counts()
    print(file_counts)
    print()
    
    # 按交易类型分析
    print("2. 交易类型分析:")
    # 提取交易类型关键词
    yingjiaheng_df['交易类型'] = yingjiaheng_df['摘要'].apply(lambda x: 
        '废料收入' if '废料' in str(x) else 
        '货款收入' if '货款' in str(x) else 
        '其他收入' if '收入' in str(x) else 
        '付款' if '收' in str(x) and '款' in str(x) else 
        '其他'
    )
    
    transaction_counts = yingjiaheng_df['交易类型'].value_counts()
    print(transaction_counts)
    print()
    
    # 金额分析
    print("3. 交易金额统计:")
    total_debit = yingjiaheng_df['借方金额'].sum()
    total_credit = yingjiaheng_df['贷方金额'].sum()
    print(f"总借方金额: {total_debit:,.2f}")
    print(f"总贷方金额: {total_credit:,.2f}")
    print()
    
    # 按科目分析
    print("4. 主要科目分析:")
    account_analysis = yingjiaheng_df.groupby('科目全名').agg({
        '借方金额': ['sum', 'count'],
        '贷方金额': ['sum', 'count']
    }).round(2)
    
    # 过滤掉空值
    account_analysis = account_analysis[(account_analysis[('借方金额', 'sum')] > 0) | 
                                       (account_analysis[('贷方金额', 'sum')] > 0)]
    
    print(account_analysis)
    print()
    
    # 时间分布
    print("5. 交易时间分布:")
    yingjiaheng_df['日期'] = pd.to_datetime(yingjiaheng_df['日期'])
    monthly_transactions = yingjiaheng_df.groupby(yingjiaheng_df['日期'].dt.to_period('M')).size()
    print(monthly_transactions)
    print()
    
    # 详细交易列表
    print("6. 前10笔详细交易:")
    detailed_transactions = yingjiaheng_df[['日期', '凭证字', '凭证号', '摘要', '科目全名', 
                                          '借方金额', '贷方金额', '文件来源']]
    print(detailed_transactions.head(10))
    
    return yingjiaheng_df

def analyze_carbon_fiber_company():
    """分析碳纤维公司数据"""
    
    balance_file = "/home/Fieons/Audit-p/format-data/financial/final_enhanced_balance.csv"
    df_balance = pd.read_csv(balance_file)
    
    # 筛选碳纤维公司
    carbon_fiber_df = df_balance[df_balance['公司'] == '广州金发碳纤维新材料发展有限公司']
    
    print("\n=== 碳纤维公司财务数据分析 ===\n")
    
    # 基本统计
    print(f"总记录数: {len(carbon_fiber_df)}")
    print(f"数据年份: {carbon_fiber_df['年份'].unique()}")
    
    # 主要科目余额
    print("\n主要科目期末余额统计:")
    major_accounts = carbon_fiber_df[~carbon_fiber_df['科目编码'].isna()]
    major_accounts = major_accounts[major_accounts['科目编码'].str.len() <= 4]  # 主要一级科目
    
    account_balance = major_accounts.groupby(['科目编码', '科目名称']).agg({
        '期末余额借方': 'sum',
        '期末余额贷方': 'sum'
    }).round(2)
    
    print(account_balance.head(10))

def analyze_composite_company():
    """分析复合材料公司数据"""
    
    balance_file = "/home/Fieons/Audit-p/format-data/financial/final_enhanced_balance.csv"
    df_balance = pd.read_csv(balance_file)
    
    # 筛选复合材料公司
    composite_df = df_balance[df_balance['公司'] == '广东金发复合材料有限公司']
    
    print("\n=== 复合材料公司财务数据分析 ===\n")
    
    # 基本统计
    print(f"总记录数: {len(composite_df)}")
    print(f"数据年份: {composite_df['年份'].unique()}")
    
    # 主要科目余额
    print("\n主要科目期末余额统计:")
    major_accounts = composite_df[~composite_df['科目编码'].isna()]
    major_accounts = major_accounts[major_accounts['科目编码'].str.len() <= 4]  # 主要一级科目
    
    account_balance = major_accounts.groupby(['科目编码', '科目名称']).agg({
        '期末余额借方': 'sum',
        '期末余额贷方': 'sum'
    }).round(2)
    
    print(account_balance.head(10))

def main():
    """主函数"""
    print("详细财务数据分析报告")
    print("=" * 50)
    
    # 分析盈骄恒交易
    yingjiaheng_df = analyze_yingjiaheng_transactions()
    
    # 分析碳纤维公司
    analyze_carbon_fiber_company()
    
    # 分析复合材料公司
    analyze_composite_company()
    
    print("\n=== 详细分析完成 ===")

if __name__ == "__main__":
    main()