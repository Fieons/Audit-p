#!/usr/bin/env python3
"""
查询与特定公司相关的凭证明细数据
目标公司：广州盈骄恒贸易有限公司、佛山市盈娇恒新材料有限公司
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def query_company_vouchers():
    """查询与目标公司相关的所有凭证明细数据"""
    
    # 数据文件路径
    input_file = "/home/Fieons/Audit-p/format-data/financial/final_voucher_detail.csv"
    output_file = "/home/Fieons/Audit-p/operation/output/company_voucher_details.csv"
    
    print(f"读取凭证明细数据：{input_file}")
    
    try:
        # 读取凭证明细数据
        df = pd.read_csv(input_file)
        print(f"总凭证明细记录数：{len(df)}")
        print(f"数据列：{list(df.columns)}")
        
        # 目标公司名称
        target_companies = [
            "广州盈骄恒贸易有限公司",
            "佛山市盈娇恒新材料有限公司"
        ]
        
        # 在摘要字段中搜索公司名称
        company_filter = df['摘要'].str.contains('|'.join(target_companies), na=False, case=False)
        
        # 同时也检查科目全名中是否包含这些公司
        subject_filter = df['科目全名'].str.contains('|'.join(target_companies), na=False, case=False)
        
        # 合并过滤条件
        combined_filter = company_filter | subject_filter
        
        # 筛选相关记录
        filtered_df = df[combined_filter].copy()
        
        print(f"找到相关凭证明细记录数：{len(filtered_df)}")
        
        if len(filtered_df) == 0:
            print("未找到相关记录，尝试更宽泛的搜索...")
            # 尝试更宽泛的搜索
            broader_keywords = ["盈骄恒", "盈娇恒", "广州盈", "佛山市盈"]
            broader_filter = df['摘要'].str.contains('|'.join(broader_keywords), na=False, case=False)
            broader_subject_filter = df['科目全名'].str.contains('|'.join(broader_keywords), na=False, case=False)
            broader_combined_filter = broader_filter | broader_subject_filter
            filtered_df = df[broader_combined_filter].copy()
            print(f"宽泛搜索找到记录数：{len(filtered_df)}")
        
        if len(filtered_df) > 0:
            # 添加公司匹配信息
            def identify_company(row):
                text = str(row['摘要']) + " " + str(row['科目全名'])
                if "广州盈骄恒贸易有限公司" in text:
                    return "广州盈骄恒贸易有限公司"
                elif "佛山市盈娇恒新材料有限公司" in text:
                    return "佛山市盈娇恒新材料有限公司"
                elif "盈骄恒" in text or "盈娇恒" in text:
                    return "疑似相关公司"
                else:
                    return "未明确"
            
            filtered_df['匹配公司'] = filtered_df.apply(identify_company, axis=1)
            
            # 提取对方单位信息
            def extract_counterpart(summary):
                if pd.isna(summary):
                    return ""
                # 从摘要中提取对方单位（通常在"/"后面）
                if "/" in summary:
                    parts = summary.split("/")
                    if len(parts) > 1:
                        return parts[1].strip()
                return ""
            
            filtered_df['对方单位'] = filtered_df['摘要'].apply(extract_counterpart)
            
            # 识别业务类型
            def identify_business_type(summary):
                if pd.isna(summary):
                    return "未知"
                summary_lower = summary.lower()
                if any(keyword in summary_lower for keyword in ["废料", "处置", "回收"]):
                    return "废料处置"
                elif any(keyword in summary_lower for keyword in ["采购", "购买", "材料"]):
                    return "材料采购"
                elif any(keyword in summary_lower for keyword in ["销售", "货款", "收款"]):
                    return "销售收款"
                elif any(keyword in summary_lower for keyword in ["付款", "支付"]):
                    return "付款业务"
                else:
                    return "其他业务"
            
            filtered_df['业务类型识别'] = filtered_df['摘要'].apply(identify_business_type)
            
            # 创建详细交易清单
            result_columns = [
                '日期',
                '凭证字',
                '凭证号',
                '摘要',
                '科目编码',
                '科目全名',
                '借方金额',
                '贷方金额',
                '匹配公司',
                '对方单位',
                '业务类型识别',
                '业务类型',
                '会计年度',
                '期间',
                '币别',
                '原币金额',
                '制单',
                '审核',
                '公司',
                '凭证唯一标识'
            ]
            
            # 确保所有列都存在
            available_columns = [col for col in result_columns if col in filtered_df.columns]
            result_df = filtered_df[available_columns].copy()
            
            # 按日期和凭证号排序
            result_df = result_df.sort_values(['日期', '凭证字', '凭证号'])
            
            # 保存结果
            result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"结果已保存到：{output_file}")
            
            # 打印统计信息
            print("\n=== 查询结果统计 ===")
            print(f"总记录数：{len(result_df)}")
            print(f"涉及凭证数：{result_df['凭证唯一标识'].nunique()}")
            print(f"时间范围：{result_df['日期'].min()} 至 {result_df['日期'].max()}")
            
            # 按匹配公司统计
            print("\n按匹配公司统计：")
            company_stats = result_df['匹配公司'].value_counts()
            print(company_stats)
            
            # 按业务类型统计
            print("\n按业务类型统计：")
            business_stats = result_df['业务类型识别'].value_counts()
            print(business_stats)
            
            # 金额统计
            print("\n金额统计：")
            total_debit = result_df['借方金额'].fillna(0).sum()
            total_credit = result_df['贷方金额'].fillna(0).sum()
            print(f"借方金额合计：{total_debit:,.2f}")
            print(f"贷方金额合计：{total_credit:,.2f}")
            
            # 显示前几条记录
            print("\n=== 前10条记录预览 ===")
            preview_columns = ['日期', '摘要', '科目全名', '借方金额', '贷方金额', '匹配公司']
            available_preview_columns = [col for col in preview_columns if col in result_df.columns]
            print(result_df[available_preview_columns].head(10).to_string(index=False))
            
            return result_df
            
        else:
            print("未找到相关记录")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"处理过程中出现错误：{e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

if __name__ == "__main__":
    query_company_vouchers()