#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细分析广州盈骄恒和佛山盈娇恒2023-2024年还款记录
"""

import pandas as pd

# 设置文件路径
voucher_file = "/home/Fieons/Audit-p/format-data/financial/final_voucher_detail.csv"

def get_detailed_repayment_records():
    """获取详细的还款记录"""
    
    print("正在读取凭证明细数据...")
    
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
        repayment_df.loc[:, '年份'] = pd.to_datetime(repayment_df['日期']).dt.year
        
        # 筛选2023和2024年的数据
        repayment_2023_2024 = repayment_df[repayment_df['年份'].isin([2023, 2024])]
        
        if not repayment_2023_2024.empty:
            print("\n=== 广州盈骄恒和佛山盈娇恒2023-2024年详细还款记录 ===")
            
            # 按日期排序
            repayment_2023_2024 = repayment_2023_2024.sort_values('日期')
            
            # 显示所有相关记录
            total_amount = 0
            for _, row in repayment_2023_2024.iterrows():
                amount = row['原币金额']
                total_amount += amount
                print(f"{row['日期']} - {row['摘要']}: {amount:.2f}元 (凭证: {row['凭证字']}-{row['凭证号']})")
            
            print(f"\n2023-2024年总还款金额: {total_amount:.2f}元")
            print(f"共找到 {len(repayment_2023_2024)} 条还款记录")
            
            # 按年份统计
            yearly_stats = repayment_2023_2024.groupby('年份').agg({
                '原币金额': ['sum', 'count']
            }).reset_index()
            
            print("\n按年份统计:")
            for _, row in yearly_stats.iterrows():
                year = int(row['年份'])
                amount = row[('原币金额', 'sum')]
                count = row[('原币金额', 'count')]
                print(f"{year}年: {amount:.2f}元 ({count}笔)")
                
            return repayment_2023_2024
            
        else:
            print("未找到2023-2024年广州盈骄恒和佛山盈娇恒的还款记录")
            
            # 显示所有相关记录
            print("\n所有盈骄恒/盈娇恒相关记录:")
            for _, row in yjh_df.iterrows():
                print(f"{row['日期']} - {row['摘要']}: {row['原币金额']:.2f}元")
            
            return None
            
    except Exception as e:
        print(f"读取数据时出错: {e}")
        return None

def check_2023_records():
    """检查2023年是否有相关记录"""
    
    try:
        voucher_df = pd.read_csv(voucher_file)
        
        # 筛选2023年的盈骄恒/盈娇恒记录
        voucher_df['年份'] = pd.to_datetime(voucher_df['日期']).dt.year
        yjh_2023 = voucher_df[(voucher_df['年份'] == 2023) & 
                             (voucher_df['摘要'].str.contains(r'盈骄恒|盈娇恒', na=False, regex=True))]
        
        if not yjh_2023.empty:
            print("\n=== 2023年盈骄恒/盈娇恒相关记录 ===")
            for _, row in yjh_2023.iterrows():
                print(f"{row['日期']} - {row['摘要']}: {row['原币金额']:.2f}元")
        else:
            print("\n2023年没有找到盈骄恒/盈娇恒的相关记录")
            
    except Exception as e:
        print(f"检查2023年记录时出错: {e}")

if __name__ == "__main__":
    print("开始详细分析广州盈骄恒和佛山盈娇恒还款记录...")
    
    # 获取详细还款记录
    repayment_data = get_detailed_repayment_records()
    
    # 检查2023年记录
    check_2023_records()
    
    print("\n分析完成!")