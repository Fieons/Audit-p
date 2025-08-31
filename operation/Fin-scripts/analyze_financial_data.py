#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from pathlib import Path

# 设置文件路径
balance_file = "/home/Fieons/Audit-p/format-data/financial/final_enhanced_balance.csv"
voucher_file = "/home/Fieons/Audit-p/format-data/financial/final_voucher_detail.csv"

def analyze_balance_sheet():
    """分析科目余额表数据结构"""
    print("=== 科目余额表数据结构分析 ===\n")
    
    # 读取数据
    df_balance = pd.read_csv(balance_file)
    
    # 基本信息
    print(f"总行数: {len(df_balance)}")
    print(f"列数: {len(df_balance.columns)}")
    print(f"列名: {list(df_balance.columns)}")
    print(f"数据类型:\n{df_balance.dtypes}")
    
    # 公司分布
    company_counts = df_balance['公司'].value_counts()
    print(f"\n公司分布:\n{company_counts}")
    
    # 年份分布
    year_counts = df_balance['年份'].value_counts()
    print(f"\n年份分布:\n{year_counts}")
    
    # 样本数据
    print("\n样本数据（前5行）:")
    print(df_balance.head())
    
    return df_balance

def analyze_voucher_detail():
    """分析凭证明细数据结构"""
    print("\n=== 凭证明细数据结构分析 ===\n")
    
    # 读取数据
    df_voucher = pd.read_csv(voucher_file)
    
    # 基本信息
    print(f"总行数: {len(df_voucher)}")
    print(f"列数: {len(df_voucher.columns)}")
    print(f"列名: {list(df_voucher.columns)}")
    print(f"数据类型:\n{df_voucher.dtypes}")
    
    # 文件来源分布
    file_counts = df_voucher['文件来源'].value_counts()
    print(f"\n文件来源分布:\n{file_counts}")
    
    # 样本数据
    print("\n样本数据（前5行）:")
    print(df_voucher.head())
    
    return df_voucher

def analyze_target_companies(df_balance, df_voucher):
    """分析目标公司数据"""
    print("\n=== 目标公司数据分析 ===\n")
    
    # 碳纤维公司分析
    carbon_fiber_companies = df_balance[df_balance['公司'].str.contains('碳纤维', na=False)]
    print(f"碳纤维相关公司记录数: {len(carbon_fiber_companies)}")
    
    # 复合材料公司分析
    composite_companies = df_balance[df_balance['公司'].str.contains('复合材料', na=False)]
    print(f"复合材料相关公司记录数: {len(composite_companies)}")
    
    # 盈骄恒公司分析
    yingjiaheng_companies = df_balance[df_balance['核算维度名称'].str.contains('盈骄恒|盈娇恒', na=False)]
    print(f"盈骄恒相关公司记录数: {len(yingjiaheng_companies)}")
    
    if len(yingjiaheng_companies) > 0:
        print("\n盈骄恒公司详情:")
        print(yingjiaheng_companies[['科目编码', '科目名称', '核算维度编码', '核算维度名称', 
                                   '期末余额借方', '期末余额贷方', '公司', '年份']].head(10))
    
    # 在凭证明细中查找盈骄恒
    yingjiaheng_vouchers = df_voucher[df_voucher['摘要'].str.contains('盈骄恒|盈娇恒', na=False)]
    print(f"\n凭证明细中盈骄恒相关记录数: {len(yingjiaheng_vouchers)}")
    
    if len(yingjiaheng_vouchers) > 0:
        print("\n凭证明细中盈骄恒交易详情:")
        print(yingjiaheng_vouchers[['日期', '凭证字', '凭证号', '摘要', '科目编码', '科目全名', 
                                  '借方金额', '贷方金额', '文件来源']].head(10))

def main():
    """主分析函数"""
    print("财务数据分析报告")
    print("=" * 50)
    
    # 分析科目余额表
    df_balance = analyze_balance_sheet()
    
    # 分析凭证明细
    df_voucher = analyze_voucher_detail()
    
    # 分析目标公司
    analyze_target_companies(df_balance, df_voucher)
    
    print("\n=== 分析完成 ===")

if __name__ == "__main__":
    main()