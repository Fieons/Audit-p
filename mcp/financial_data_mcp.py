#!/usr/bin/env python3
"""
MCP Server for Financial Data Query
查询format-data/financial目录下的财务数据的MCP工具
"""

import asyncio
import sys
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import re
from difflib import SequenceMatcher

from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# 数据文件路径
DATA_DIR = Path("format-data/financial")
BALANCE_FILE = DATA_DIR / "final_enhanced_balance.csv"
VOUCHER_FILE = DATA_DIR / "final_voucher_detail.csv"

# 全局数据缓存
balance_df = None
voucher_df = None

def load_data():
    """加载财务数据到内存"""
    global balance_df, voucher_df
    
    def load_csv_with_optimization(file_path, dtype_mapping, date_columns=None):
        """通用CSV加载函数，支持数据类型优化"""
        if not file_path.exists():
            raise FileNotFoundError(f"❌ 文件不存在: {file_path}\n💡 请确保数据文件位于正确的目录中")
        
        df = pd.read_csv(file_path, encoding='utf-8')
        
        # 应用数据类型转换
        for column, dtype_func in dtype_mapping.items():
            if column in df.columns:
                df[column] = dtype_func(df[column])
        
        # 处理日期列
        if date_columns:
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    
    if balance_df is None:
        balance_dtype_mapping = {
            '科目编码': lambda x: x.astype(str),
            '年份': lambda x: pd.to_numeric(x, errors='coerce')
        }
        balance_df = load_csv_with_optimization(BALANCE_FILE, balance_dtype_mapping)
    
    if voucher_df is None:
        voucher_dtype_mapping = {
            '科目编码': lambda x: x.astype(str),
            '借方金额': lambda x: pd.to_numeric(x, errors='coerce').fillna(0),
            '贷方金额': lambda x: pd.to_numeric(x, errors='coerce').fillna(0)
        }
        voucher_df = load_csv_with_optimization(VOUCHER_FILE, voucher_dtype_mapping, ['日期'])

def format_amount(amount: float) -> str:
    """格式化金额显示"""
    if pd.isna(amount) or abs(amount) < 0.01:
        return "0.00"
    return f"{amount:,.2f}"

def create_output_header(title: str, record_count: int, truncated: bool = False, limit: int = 0) -> List[str]:
    """创建输出头部信息"""
    output_lines = [f"# {title}\n"]
    output_lines.append(f"**记录数量**: {record_count}")
    
    if truncated and limit > 0:
        output_lines.append(f"\n注意：结果已截断，仅显示前{limit}条记录")
    
    output_lines.append("")
    return output_lines

def format_balance_info(row: pd.Series, include_dimension: bool = True) -> List[str]:
    """格式化余额信息"""
    lines = []
    
    # 优化核算维度显示
    if include_dimension and len(row) > 3:
        dimension_name = row.iloc[3]
        if pd.notna(dimension_name) and str(dimension_name).strip() and str(dimension_name) != 'nan':
            lines.append(f"**核算维度**: {dimension_name}")
    
    lines.append("**余额信息**:")
    balance_columns = [
        ('期初余额借方', '期初借方'),
        ('期初余额贷方', '期初贷方'),
        ('本年累计借方', '本年累计借方'),
        ('本年累计贷方', '本年累计贷方'),
        ('期末余额借方', '期末借方'),
        ('期末余额贷方', '期末贷方')
    ]
    
    for col, display_name in balance_columns:
        if col in row:
            lines.append(f"- {display_name}: {format_amount(row[col])}")
    
    return lines

def get_financial_synonyms() -> Dict[str, List[str]]:
    """获取财务术语同义词映射"""
    return {
        "固定资产": ["固定资产", "固资", "设备", "机器", "厂房", "建筑物"],
        "其他费用": ["其他费用", "其他", "杂费", "其它费用", "其它"],
        "管理费用": ["管理费用", "管理费", "行政费用", "行政费"],
        "销售费用": ["销售费用", "销售费", "营销费用", "营销费"],
        "财务费用": ["财务费用", "财务费", "利息费用", "利息"],
        "银行存款": ["银行存款", "银行", "存款", "现金"],
        "应收账款": ["应收账款", "应收", "客户欠款"],
        "应付账款": ["应付账款", "应付", "供应商欠款"]
    }

def enhanced_search_keywords(keyword: str, text_series: pd.Series) -> pd.Series:
    """增强的关键词搜索功能"""
    if pd.isna(keyword) or keyword.strip() == "":
        return pd.Series([False] * len(text_series))
    
    keyword = keyword.strip().lower()
    
    # 1. 精确匹配
    exact_match = text_series.str.contains(keyword, case=False, na=False, regex=False)
    
    # 如果精确匹配有结果，直接返回
    if exact_match.any():
        return exact_match
    
    # 2. 同义词匹配
    synonyms = get_financial_synonyms()
    synonym_match = pd.Series([False] * len(text_series))
    
    for main_term, synonym_list in synonyms.items():
        if keyword in [syn.lower() for syn in synonym_list] or \
           any(syn.lower() in keyword for syn in synonym_list):
            for syn in synonym_list:
                synonym_match |= text_series.str.contains(syn, case=False, na=False, regex=False)
    
    if synonym_match.any():
        return synonym_match
    
    # 3. 模糊匹配（相似度阈值0.6）
    fuzzy_match = pd.Series([False] * len(text_series))
    for idx, text in text_series.items():
        if pd.notna(text):
            text_lower = str(text).lower()
            similarity = SequenceMatcher(None, keyword, text_lower).ratio()
            if similarity >= 0.6:
                fuzzy_match.iloc[idx] = True
    
    return exact_match | synonym_match | fuzzy_match

def cross_validate_balance_voucher(subject_code: str, company: str = None, year: int = None) -> Dict[str, Any]:
    """交叉验证余额表和凭证明细数据一致性"""
    global balance_df, voucher_df
    
    validation_result = {
        "subject_code": subject_code,
        "validation_passed": False,
        "balance_data": None,
        "voucher_summary": None,
        "differences": [],
        "warnings": []
    }
    
    try:
        # 查询余额表数据
        balance_filter = {"subject_code": subject_code}
        if company:
            balance_filter["company"] = company
        if year:
            balance_filter["year"] = year
            
        balance_result = filter_dataframe(balance_df, balance_filter)
        
        # 查询凭证明细数据
        voucher_filter = {"subject_code": subject_code}
        if company:
            voucher_filter["company"] = company
        voucher_result = filter_dataframe(voucher_df, voucher_filter)
        
        # 年份筛选（凭证明细需要单独处理）
        if year:
            voucher_result = voucher_result[voucher_result["日期"].dt.year == year]
        
        if balance_result.empty and voucher_result.empty:
            validation_result["warnings"].append(f"科目 {subject_code} 在余额表和凭证明细中均无数据")
            return validation_result
        
        if balance_result.empty:
            validation_result["warnings"].append(f"科目 {subject_code} 在余额表中无数据")
            return validation_result
            
        if voucher_result.empty:
            validation_result["warnings"].append(f"科目 {subject_code} 在凭证明细中无数据")
            return validation_result
        
        # 计算余额表汇总
        balance_summary = {
            "total_debit": balance_result["本年累计借方"].sum(),
            "total_credit": balance_result["本年累计贷方"].sum(),
            "ending_debit": balance_result["期末余额借方"].sum(),
            "ending_credit": balance_result["期末余额贷方"].sum()
        }
        
        # 计算凭证明细汇总
        voucher_summary = {
            "total_debit": voucher_result["借方金额"].sum(),
            "total_credit": voucher_result["贷方金额"].sum(),
            "net_amount": voucher_result["借方金额"].sum() - voucher_result["贷方金额"].sum()
        }
        
        validation_result["balance_data"] = balance_summary
        validation_result["voucher_summary"] = voucher_summary
        
        # 验证数据一致性（允许小数误差）
        debit_diff = abs(balance_summary["total_debit"] - voucher_summary["total_debit"])
        credit_diff = abs(balance_summary["total_credit"] - voucher_summary["total_credit"])
        
        if debit_diff > 0.01:
            validation_result["differences"].append(f"借方金额不匹配：余额表{format_amount(balance_summary['total_debit'])} vs 凭证明细{format_amount(voucher_summary['total_debit'])}")
            
        if credit_diff > 0.01:
            validation_result["differences"].append(f"贷方金额不匹配：余额表{format_amount(balance_summary['total_credit'])} vs 凭证明细{format_amount(voucher_summary['total_credit'])}")
        
        validation_result["validation_passed"] = len(validation_result["differences"]) == 0
        
    except Exception as e:
        validation_result["warnings"].append(f"验证过程出错：{str(e)}")
    
    return validation_result

def filter_dataframe(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """通用数据框筛选函数"""
    result = df.copy()
    
    # 列名映射配置
    column_mapping = {
        "company": "公司",
        "period": "期间", 
        "subject_code": "科目编码",
        "subject_path": "subject_code_path",
        "year": "年份",
        "dimension_name": df.columns[3] if len(df.columns) > 3 else None,
        "subject_name_path": "subject_name_path"
    }
    
    for key, value in filters.items():
        if value is None or value == "":
            continue
            
        column_name = column_mapping.get(key)
        if not column_name or column_name not in df.columns:
            continue
            
        if key == "subject_path":
            # 处理科目路径查询
            path_value = str(value).strip()
            if not path_value.startswith("/"):
                path_value = "/" + path_value
            if not path_value.endswith("/"):
                path_value = path_value + "/"
            result = result[result[column_name].str.contains(re.escape(path_value), case=False, na=False)]
        elif key == "year":
            result = result[result[column_name] == int(value)]
        else:
            # 通用字符串包含匹配
            result = result[result[column_name].str.contains(str(value), case=False, na=False)]
    
    return result

app = Server("financial-data-query")

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """返回可用的工具列表"""
    return [
        types.Tool(
            name="query_balance_sheet",
            description="查询科目余额表数据，支持按公司、期间、科目等条件筛选",
            inputSchema={
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "公司名称（支持部分匹配）"
                    },
                    "period": {
                        "type": "string", 
                        "description": "会计期间"
                    },
                    "subject_code": {
                        "type": "string",
                        "description": "科目编码（支持部分匹配）"
                    },
                    "subject_path": {
                        "type": "string",
                        "description": "科目路径（如：/1002/ 查询银行存款及其子科目）"
                    },
                    "dimension_name": {
                        "type": "string",
                        "description": "核算维度名称（如：供应商、客户、部门、项目等）"
                    },
                    "subject_name_path": {
                        "type": "string",
                        "description": "科目名称路径（如：/银行存款/ 查询银行存款及其子科目）"
                    },
                    "year": {
                        "type": "integer",
                        "description": "年份"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量限制",
                        "default": 100
                    },
                    "include_dimensions": {
                        "type": "boolean",
                        "description": "是否包含核算维度明细",
                        "default": False
                    }
                }
            }
        ),
        types.Tool(
            name="query_voucher_details", 
            description="查询凭证明细数据，支持按日期、科目、金额等条件筛选",
            inputSchema={
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "公司名称（支持部分匹配）"
                    },
                    "subject_code": {
                        "type": "string", 
                        "description": "科目编码（支持部分匹配）"
                    },
                    "date_start": {
                        "type": "string",
                        "description": "开始日期 (YYYY-MM-DD)"
                    },
                    "date_end": {
                        "type": "string", 
                        "description": "结束日期 (YYYY-MM-DD)"
                    },
                    "voucher_no": {
                        "type": "string",
                        "description": "凭证号"
                    },
                    "amount_min": {
                        "type": "number",
                        "description": "最小金额"
                    },
                    "amount_max": {
                        "type": "number", 
                        "description": "最大金额"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量限制",
                        "default": 100
                    }
                }
            }
        ),
        types.Tool(
            name="analyze_subject_hierarchy",
            description="分析科目层级结构，显示指定科目的子科目和汇总信息",
            inputSchema={
                "type": "object", 
                "properties": {
                    "subject_code": {
                        "type": "string",
                        "description": "父级科目编码（如：1002 查询银行存款的所有子科目）"
                    },
                    "company": {
                        "type": "string",
                        "description": "公司名称（支持部分匹配）"
                    },
                    "year": {
                        "type": "integer",
                        "description": "年份"
                    }
                },
                "required": ["subject_code"]
            }
        ),
        types.Tool(
            name="get_financial_summary",
            description="获取财务数据汇总统计信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string", 
                        "description": "公司名称（支持部分匹配）"
                    },
                    "year": {
                        "type": "integer",
                        "description": "年份"
                    },
                    "summary_type": {
                        "type": "string",
                        "enum": ["balance", "voucher", "both"],
                        "description": "汇总类型：balance(余额表), voucher(凭证), both(两者)",
                        "default": "both"
                    }
                }
            }
        ),
        types.Tool(
            name="validate_data_consistency",
            description="验证科目余额表和凭证明细数据的一致性",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject_code": {
                        "type": "string",
                        "description": "科目编码"
                    },
                    "company": {
                        "type": "string",
                        "description": "公司名称（支持部分匹配）"
                    },
                    "year": {
                        "type": "integer",
                        "description": "年份"
                    }
                },
                "required": ["subject_code"]
            }
        ),
        types.Tool(
            name="search_transactions",
            description="搜索特定的交易记录，支持关键词搜索摘要内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "搜索关键词（在摘要中搜索）"
                    },
                    "company": {
                        "type": "string",
                        "description": "公司名称（支持部分匹配）"
                    },
                    "date_start": {
                        "type": "string",
                        "description": "开始日期 (YYYY-MM-DD)"
                    },
                    "date_end": {
                        "type": "string",
                        "description": "结束日期 (YYYY-MM-DD)"
                    },
                    "limit": {
                        "type": "integer", 
                        "description": "返回结果数量限制",
                        "default": 50
                    }
                },
                "required": ["keyword"]
            }
        ),
        types.Tool(
            name="find_subject_by_name",
            description="通过科目名称智能查找对应的科目编码和层级信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject_name": {
                        "type": "string",
                        "description": "科目名称（如：其他应付款、银行存款、应收账款等）"
                    },
                    "company": {
                        "type": "string",
                        "description": "公司名称（支持部分匹配）"
                    },
                    "fuzzy_match": {
                        "type": "boolean",
                        "description": "是否启用模糊匹配",
                        "default": True
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量限制",
                        "default": 20
                    }
                },
                "required": ["subject_name"]
            }
        ),
        types.Tool(
            name="query_dimension_details",
            description="查询指定科目的核算维度明细信息，支持多种维度类型",
            inputSchema={
                "type": "object",
                "properties": {
                    "subject_code": {
                        "type": "string",
                        "description": "科目编码（如：2202应付账款、1122应收账款等）"
                    },
                    "company": {
                        "type": "string",
                        "description": "公司名称（支持部分匹配）"
                    },
                    "year": {
                        "type": "integer",
                        "description": "年份"
                    },
                    "dimension_type": {
                        "type": "string",
                        "description": "维度类型筛选（如：供应商、客户、部门等，留空则查询所有类型）"
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["ending_balance", "total_debit", "total_credit", "dimension_name"],
                        "description": "排序方式：ending_balance(期末余额), total_debit(借方总额), total_credit(贷方总额), dimension_name(维度名称)",
                        "default": "ending_balance"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量限制",
                        "default": 100
                    },
                    "show_zero_balance": {
                        "type": "boolean",
                        "description": "是否显示余额为零的维度",
                        "default": False
                    }
                },
                "required": ["subject_code"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """处理工具调用"""
    try:
        load_data()
        
        if name == "query_balance_sheet":
            return await query_balance_sheet(arguments)
        elif name == "query_voucher_details":
            return await query_voucher_details(arguments)
        elif name == "analyze_subject_hierarchy":
            return await analyze_subject_hierarchy(arguments)
        elif name == "get_financial_summary":
            return await get_financial_summary(arguments)
        elif name == "search_transactions":
            return await search_transactions(arguments)
        elif name == "validate_data_consistency":
            return await validate_data_consistency(arguments)
        elif name == "find_subject_by_name":
            return await find_subject_by_name(arguments)
        elif name == "query_dimension_details":
            return await query_dimension_details(arguments)
        else:
            raise ValueError(f"未知工具: {name}")
            
    except Exception as e:
        error_msg = f"执行工具 '{name}' 时发生错误: {str(e)}"
        print(f"Tool execution error: {error_msg}", file=sys.stderr)
        
        # 提供更友好的错误提示
        if "not found" in str(e).lower() or "file not exist" in str(e).lower():
            error_msg += "\n\n💡 建议：请检查数据文件是否存在，或联系系统管理员。"
        elif "invalid" in str(e).lower():
            error_msg += "\n\n💡 建议：请检查输入参数格式是否正确。"
        elif "connection" in str(e).lower():
            error_msg += "\n\n💡 建议：请检查网络连接或数据库连接。"
        else:
            error_msg += "\n\n💡 建议：如果问题持续存在，请联系技术支持。"
        
        return [types.TextContent(type="text", text=error_msg)]

async def query_balance_sheet(args: dict) -> list[types.TextContent]:
    """查询科目余额表"""
    global balance_df
    
    # 应用筛选条件
    result = filter_dataframe(balance_df, args)
    
    # 限制返回数量
    limit = args.get("limit", 100)
    truncated = len(result) > limit
    if truncated:
        result = result.head(limit)
    
    if result.empty:
        suggestion = "💡 建议：\n"
        suggestion += "- 检查科目编码是否正确\n"
        suggestion += "- 尝试使用部分匹配（如：输入'1601'查找固定资产相关科目）\n"
        suggestion += "- 检查公司名称和年份参数是否正确\n"
        suggestion += "- 使用 get_financial_summary 工具查看可用的数据范围"
        return [types.TextContent(type="text", text=f"❌ 未找到符合条件的余额记录\n\n{suggestion}")]
    
    # 格式化输出
    output_lines = create_output_header("科目余额表查询结果", len(result), truncated, limit)
    
    for _, row in result.iterrows():
        subject_code = str(row['科目编码']) if pd.notna(row['科目编码']) else "未知编码"
        subject_name = str(row['科目名称']) if pd.notna(row['科目名称']) else "未知名称"
        
        output_lines.append(f"## 科目: {subject_code} - {subject_name}")
        output_lines.append(f"**公司**: {row['公司']}")
        output_lines.append(f"**期间**: {row['期间']}")
        
        # 添加余额信息
        output_lines.extend(format_balance_info(row))
        output_lines.append("")
    
    return [types.TextContent(type="text", text="\n".join(output_lines))]

async def query_voucher_details(args: dict) -> list[types.TextContent]:
    """查询凭证明细"""
    global voucher_df
    
    # 使用统一的筛选函数
    voucher_filters = {}
    for key in ['company', 'subject_code', 'voucher_no']:
        if args.get(key):
            voucher_filters[key] = args[key]
    
    result = filter_dataframe(voucher_df, voucher_filters)
    
    # 处理日期范围筛选
    if args.get("date_start"):
        start_date = pd.to_datetime(args["date_start"])
        result = result[result["日期"] >= start_date]
    
    if args.get("date_end"):
        end_date = pd.to_datetime(args["date_end"])
        result = result[result["日期"] <= end_date]
    
    # 处理金额范围筛选
    if args.get("amount_min"):
        amount_min = args["amount_min"]
        result = result[(result["借方金额"] >= amount_min) | (result["贷方金额"] >= amount_min)]
    
    if args.get("amount_max"):
        amount_max = args["amount_max"]
        result = result[(result["借方金额"] <= amount_max) | (result["贷方金额"] <= amount_max)]
    
    # 限制返回数量
    limit = args.get("limit", 100)
    truncated = len(result) > limit
    if truncated:
        result = result.head(limit)
    
    if result.empty:
        suggestion = "💡 建议：\n"
        suggestion += "- 检查日期范围是否正确\n"
        suggestion += "- 尝试扩大搜索范围（如：减少筛选条件）\n"
        suggestion += "- 检查科目编码格式\n"
        suggestion += "- 使用 search_transactions 工具通过关键词搜索"
        return [types.TextContent(type="text", text=f"❌ 未找到符合条件的凭证记录\n\n{suggestion}")]
    
    # 格式化输出
    output_lines = create_output_header("凭证明细查询结果", len(result), truncated, limit)
    
    current_voucher = None
    for _, row in result.iterrows():
        voucher_key = f"{row['凭证字']}-{row['凭证号']}"
        
        if current_voucher != voucher_key:
            current_voucher = voucher_key
            output_lines.append(f"## 凭证: {voucher_key}")
            output_lines.append(f"**日期**: {row['日期'].strftime('%Y-%m-%d') if pd.notna(row['日期']) else 'N/A'}")
            output_lines.append("")
        
        output_lines.append(f"### 分录 {row['分录行号']}")
        output_lines.append(f"**摘要**: {row['摘要']}")
        output_lines.append(f"**科目**: {row['科目编码']} - {row['科目全名']}")
        output_lines.append(f"**借方**: {format_amount(row['借方金额'])}")
        output_lines.append(f"**贷方**: {format_amount(row['贷方金额'])}")
        output_lines.append("")
    
    return [types.TextContent(type="text", text="\n".join(output_lines))]

async def analyze_subject_hierarchy(args: dict) -> list[types.TextContent]:
    """分析科目层级结构"""
    global balance_df
    
    subject_code = args["subject_code"]
    
    # 使用统一的筛选函数
    filters = {"subject_path": f"/{subject_code}/"}
    if args.get("company"):
        filters["company"] = args["company"]
    if args.get("year"):
        filters["year"] = args["year"]
    
    result = filter_dataframe(balance_df, filters)
    
    if result.empty:
        return [types.TextContent(type="text", text=f"未找到科目编码 {subject_code} 的相关记录")]
    
    # 按科目路径层级排序
    result = result.sort_values("subject_code_path")
    
    # 计算汇总信息
    total_debit_balance = result["期末余额借方"].sum()
    total_credit_balance = result["期末余额贷方"].sum()
    total_debit_amount = result["本年累计借方"].sum()
    total_credit_amount = result["本年累计贷方"].sum()
    
    # 格式化输出
    output_lines = [f"# 科目层级分析: {subject_code}\n"]
    output_lines.append("## 汇总信息")
    output_lines.append(f"**子科目数量**: {len(result)}")
    output_lines.append(f"**期末余额借方合计**: {format_amount(total_debit_balance)}")
    output_lines.append(f"**期末余额贷方合计**: {format_amount(total_credit_balance)}")
    output_lines.append(f"**本年累计借方合计**: {format_amount(total_debit_amount)}")
    output_lines.append(f"**本年累计贷方合计**: {format_amount(total_credit_amount)}")
    output_lines.append("")
    
    output_lines.append("## 明细科目")
    for _, row in result.iterrows():
        level = row["subject_code_path"].count("/") - 2 if pd.notna(row.get("subject_code_path")) else 0  # 计算层级深度
        indent = "  " * max(0, level)
        
        # 处理科目编码和名称的显示
        subject_code = str(row['科目编码']) if pd.notna(row['科目编码']) else "未知编码"
        subject_name = str(row['科目名称']) if pd.notna(row['科目名称']) else "未知名称"
        
        output_lines.append(f"{indent}- **{subject_code}** {subject_name}")
        output_lines.append(f"{indent}  - 期末借方: {format_amount(row['期末余额借方'])}")
        output_lines.append(f"{indent}  - 期末贷方: {format_amount(row['期末余额贷方'])}")
        
        # 优化核算维度显示
        dimension_name = row.get(df.columns[3])
        if pd.notna(dimension_name) and str(dimension_name).strip() and str(dimension_name) != 'nan':
            output_lines.append(f"{indent}  - 核算维度: {dimension_name}")
    
    return [types.TextContent(type="text", text="\n".join(output_lines))]

async def get_financial_summary(args: dict) -> list[types.TextContent]:
    """获取财务数据汇总"""
    global balance_df, voucher_df
    
    summary_type = args.get("summary_type", "both")
    output_lines = ["# 财务数据汇总报告\n"]
    
    # 余额表汇总
    if summary_type in ["balance", "both"]:
        # 使用统一的筛选函数
        balance_filters = {}
        if args.get("company"):
            balance_filters["company"] = args["company"]
        if args.get("year"):
            balance_filters["year"] = args["year"]
        
        balance_data = filter_dataframe(balance_df, balance_filters)
        
        output_lines.append("## 科目余额表汇总")
        output_lines.append(f"**总记录数**: {len(balance_data):,}")
        output_lines.append(f"**公司数量**: {balance_data['公司'].nunique()}")
        output_lines.append(f"**期间范围**: {balance_data['期间'].min()} - {balance_data['期间'].max()}")
        output_lines.append(f"**年份范围**: {balance_data['年份'].min()} - {balance_data['年份'].max()}")
        
        # 按公司统计
        company_stats = balance_data.groupby("公司").size()
        output_lines.append("\n**按公司统计**:")
        for company, count in company_stats.items():
            output_lines.append(f"- {company}: {count:,} 条记录")
        
        output_lines.append("")
    
    # 凭证明细汇总
    if summary_type in ["voucher", "both"]:
        # 使用统一的筛选函数
        voucher_filters = {}
        if args.get("company"):
            voucher_filters["company"] = args["company"]
        
        voucher_data = filter_dataframe(voucher_df, voucher_filters)
        
        # 添加年份筛选
        if args.get("year"):
            voucher_data = voucher_data[voucher_data["日期"].dt.year == args["year"]]
        
        output_lines.append("## 凭证明细汇总")
        output_lines.append(f"**总记录数**: {len(voucher_data):,}")
        output_lines.append(f"**公司数量**: {voucher_data['公司'].nunique()}")
        
        if len(voucher_data) > 0:
            output_lines.append(f"**日期范围**: {voucher_data['日期'].min().strftime('%Y-%m-%d')} - {voucher_data['日期'].max().strftime('%Y-%m-%d')}")
            output_lines.append(f"**凭证数量**: {voucher_data['凭证唯一标识'].nunique():,}")
            
            total_debit = voucher_data["借方金额"].sum()
            total_credit = voucher_data["贷方金额"].sum()
            output_lines.append(f"**借方金额合计**: {format_amount(total_debit)}")
            output_lines.append(f"**贷方金额合计**: {format_amount(total_credit)}")
        
        # 按公司统计
        company_stats = voucher_data.groupby("公司").size()
        output_lines.append("\n**按公司统计**:")
        for company, count in company_stats.items():
            output_lines.append(f"- {company}: {count:,} 条记录")
    
    return [types.TextContent(type="text", text="\n".join(output_lines))]

async def search_transactions(args: dict) -> list[types.TextContent]:
    """搜索交易记录"""
    global voucher_df
    
    keyword = args["keyword"]
    # 使用增强搜索算法
    search_mask = enhanced_search_keywords(keyword, voucher_df["摘要"])
    result = voucher_df[search_mask]
    
    # 使用统一的筛选函数
    filters = {}
    if args.get("company"):
        filters["company"] = args["company"]
    
    result = filter_dataframe(result, filters)
    
    # 处理日期范围筛选
    if args.get("date_start"):
        start_date = pd.to_datetime(args["date_start"])
        result = result[result["日期"] >= start_date]
    
    if args.get("date_end"):
        end_date = pd.to_datetime(args["date_end"])
        result = result[result["日期"] <= end_date]
    
    # 限制返回数量
    limit = args.get("limit", 50)
    truncated = len(result) > limit
    if truncated:
        result = result.head(limit)
    
    if result.empty:
        suggestion = "💡 建议：\n"
        suggestion += "- 尝试使用更通用的关键词\n"
        suggestion += "- 检查关键词拼写\n"
        suggestion += "- 尝试使用同义词（如：'固定资产'、'固资'、'设备'）\n"
        suggestion += "- 扩大日期范围或减少其他筛选条件"
        return [types.TextContent(type="text", text=f"❌ 未找到包含关键词 '{keyword}' 的交易记录\n\n{suggestion}")]
    
    # 格式化输出
    output_lines = create_output_header(f"交易搜索结果: '{keyword}'", len(result), truncated, limit)
    
    for _, row in result.iterrows():
        output_lines.append(f"## {row['日期'].strftime('%Y-%m-%d') if pd.notna(row['日期']) else 'N/A'} | {row['凭证字']}-{row['凭证号']}")
        output_lines.append(f"**摘要**: {row['摘要']}")
        output_lines.append(f"**科目**: {row['科目编码']} - {row['科目全名']}")
        output_lines.append(f"**金额**: 借方 {format_amount(row['借方金额'])} | 贷方 {format_amount(row['贷方金额'])}")
        output_lines.append(f"**公司**: {row['公司']}")
        output_lines.append("")
    
    return [types.TextContent(type="text", text="\n".join(output_lines))]

async def validate_data_consistency(args: dict) -> list[types.TextContent]:
    """验证数据一致性"""
    subject_code = args["subject_code"]
    company = args.get("company")
    year = args.get("year")
    
    validation_result = cross_validate_balance_voucher(subject_code, company, year)
    
    # 格式化输出
    output_lines = [f"# 数据一致性验证报告: {subject_code}\n"]
    
    if validation_result["validation_passed"]:
        output_lines.append("## ✅ 验证结果：通过")
        output_lines.append("余额表和凭证明细数据一致")
    else:
        output_lines.append("## ❌ 验证结果：失败")
        
    # 显示警告信息
    if validation_result["warnings"]:
        output_lines.append("\n## ⚠️ 警告信息")
        for warning in validation_result["warnings"]:
            output_lines.append(f"- {warning}")
    
    # 显示差异信息
    if validation_result["differences"]:
        output_lines.append("\n## 🔍 数据差异")
        for diff in validation_result["differences"]:
            output_lines.append(f"- {diff}")
    
    # 显示详细数据对比
    if validation_result["balance_data"] and validation_result["voucher_summary"]:
        balance_data = validation_result["balance_data"]
        voucher_data = validation_result["voucher_summary"]
        
        output_lines.append("\n## 📊 数据对比")
        output_lines.append("\n### 余额表数据")
        output_lines.append(f"- 本年累计借方：{format_amount(balance_data['total_debit'])}")
        output_lines.append(f"- 本年累计贷方：{format_amount(balance_data['total_credit'])}")
        output_lines.append(f"- 期末余额借方：{format_amount(balance_data['ending_debit'])}")
        output_lines.append(f"- 期末余额贷方：{format_amount(balance_data['ending_credit'])}")
        
        output_lines.append("\n### 凭证明细数据")
        output_lines.append(f"- 借方金额合计：{format_amount(voucher_data['total_debit'])}")
        output_lines.append(f"- 贷方金额合计：{format_amount(voucher_data['total_credit'])}")
        output_lines.append(f"- 净额：{format_amount(voucher_data['net_amount'])}")
    
    return [types.TextContent(type="text", text="\n".join(output_lines))]

async def find_subject_by_name(args: dict) -> list[types.TextContent]:
    """通过科目名称智能查找科目编码"""
    global balance_df
    
    subject_name = args["subject_name"].strip()
    fuzzy_match = args.get("fuzzy_match", True)
    limit = args.get("limit", 20)
    
    # 使用统一的筛选函数
    filters = {}
    if args.get("company"):
        filters["company"] = args["company"]
    
    result = filter_dataframe(balance_df, filters)
    
    # 科目名称匹配策略
    matched_subjects = []
    
    # 1. 精确匹配科目名称
    exact_matches = result[result["科目名称"].str.contains(subject_name, case=False, na=False, regex=False)]
    if not exact_matches.empty:
        matched_subjects.append(("精确匹配", exact_matches))
    
    # 2. 精确匹配科目全名
    if "科目全名" in result.columns:
        full_name_matches = result[result["科目全名"].str.contains(subject_name, case=False, na=False, regex=False)]
        if not full_name_matches.empty:
            matched_subjects.append(("全名匹配", full_name_matches))
    
    # 3. 同义词匹配
    synonyms = get_financial_synonyms()
    for main_term, synonym_list in synonyms.items():
        if subject_name in synonym_list or any(syn in subject_name for syn in synonym_list):
            for syn in synonym_list:
                syn_matches = result[result["科目名称"].str.contains(syn, case=False, na=False, regex=False)]
                if not syn_matches.empty:
                    matched_subjects.append((f"同义词匹配({syn})", syn_matches))
    
    # 4. 模糊匹配（如果启用）
    if fuzzy_match and not matched_subjects:
        # 将科目名称拆分为关键词进行匹配
        keywords = subject_name.replace("其他", "").replace("应付", "").replace("应收", "").replace("款", "").strip()
        if keywords:
            fuzzy_matches = result[result["科目名称"].str.contains(keywords, case=False, na=False, regex=False)]
            if not fuzzy_matches.empty:
                matched_subjects.append(("模糊匹配", fuzzy_matches))
    
    if not matched_subjects:
        suggestion = "💡 建议：\n"
        suggestion += f"- 检查科目名称 '{subject_name}' 是否正确\n"
        suggestion += "- 尝试使用简化名称（如：'应付' 而不是 '其他应付款'）\n"
        suggestion += "- 使用 get_financial_summary 查看可用科目\n"
        suggestion += "- 常见科目别名：银行存款、应收账款、固定资产、管理费用等"
        return [types.TextContent(type="text", text=f"❌ 未找到与 '{subject_name}' 相关的科目\n\n{suggestion}")]
    
    # 格式化输出结果
    output_lines = [f"# 科目名称查找结果: '{subject_name}'\n"]
    
    total_found = 0
    for match_type, matches in matched_subjects:
        if matches.empty:
            continue
            
        # 去重：按科目编码去重
        unique_matches = matches.drop_duplicates(subset=['科目编码'])
        
        output_lines.append(f"## {match_type}")
        output_lines.append(f"**找到 {len(unique_matches)} 个科目**\n")
        
        # 限制显示数量
        display_matches = unique_matches.head(limit // len(matched_subjects) + 1)
        
        for _, row in display_matches.iterrows():
            subject_code = str(row['科目编码']) if pd.notna(row['科目编码']) else "未知编码"
            subject_name_display = str(row['科目名称']) if pd.notna(row['科目名称']) else "未知名称"
            
            output_lines.append(f"### {subject_code} - {subject_name_display}")
            
            # 显示余额信息（汇总同科目的数据）
            same_subject = matches[matches['科目编码'] == row['科目编码']]
            total_debit = same_subject['期末余额借方'].sum()
            total_credit = same_subject['期末余额贷方'].sum()
            
            output_lines.append(f"**期末余额**: 借方 {format_amount(total_debit)} | 贷方 {format_amount(total_credit)}")
            
            # 显示层级路径（如果有）
            if pd.notna(row.get('subject_code_path')):
                output_lines.append(f"**科目路径**: {row['subject_code_path']}")
            
            # 显示公司信息
            companies = same_subject['公司'].unique()
            if len(companies) > 0:
                output_lines.append(f"**相关公司**: {', '.join(companies[:3])}")
                if len(companies) > 3:
                    output_lines.append(f"  （还有{len(companies)-3}个公司）")
            
            output_lines.append("")
            total_found += 1
            
            if total_found >= limit:
                break
        
        if total_found >= limit:
            output_lines.append(f"注意：结果已截断，仅显示前{limit}个科目")
            break
    
    # 提供使用建议
    if total_found > 0:
        output_lines.append("---")
        output_lines.append("💡 **使用建议**:")
        output_lines.append("- 复制所需的科目编码，用于 query_balance_sheet 或 query_voucher_details")
        output_lines.append("- 使用 analyze_subject_hierarchy 查看科目的完整层级结构")
        output_lines.append("- 使用科目路径（如 /2204/）可查询该科目及所有子科目")
    
    return [types.TextContent(type="text", text="\n".join(output_lines))]

async def query_dimension_details(args: dict) -> list[types.TextContent]:
    """查询核算维度明细信息"""
    global balance_df
    
    subject_code = args["subject_code"]
    company = args.get("company")
    year = args.get("year")
    dimension_type = args.get("dimension_type", "")
    sort_by = args.get("sort_by", "ending_balance")
    limit = args.get("limit", 100)
    show_zero_balance = args.get("show_zero_balance", False)
    
    # 使用统一的筛选函数
    filters = {"subject_path": f"/{subject_code}/"}
    if company:
        filters["company"] = company
    if year:
        filters["year"] = year
    
    result = filter_dataframe(balance_df, filters)
    
    # 筛选有核算维度的记录
    dimension_records = result[pd.notna(result[result.columns[3]]) & (result[result.columns[3]] != "")]
    
    if dimension_records.empty:
        suggestion = "💡 建议：\n"
        suggestion += f"- 检查科目编码 {subject_code} 是否正确\n"
        suggestion += "- 该科目可能没有设置核算维度\n"
        suggestion += "- 尝试查询其他相关科目\n"
        suggestion += "- 使用 query_balance_sheet 查看科目基本信息"
        return [types.TextContent(type="text", text=f"❌ 未找到科目 {subject_code} 的核算维度记录\n\n{suggestion}")]
    
    # 按核算维度名称分组汇总
    dimension_groups = dimension_records.groupby(dimension_records.columns[3])
    
    # 计算每个维度的汇总信息
    dimension_summary = []
    for dim_name, group in dimension_groups:
        total_debit = group["本年累计借方"].sum()
        total_credit = group["本年累计贷方"].sum()
        ending_debit = group["期末余额借方"].sum()
        ending_credit = group["期末余额贷方"].sum()
        ending_balance = ending_debit - ending_credit
        
        # 过滤零余额记录（如果不需要显示）
        if not show_zero_balance and abs(ending_balance) < 0.01:
            continue
            
        dimension_summary.append({
            "dimension_name": dim_name,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "ending_debit": ending_debit,
            "ending_credit": ending_credit,
            "ending_balance": ending_balance,
            "record_count": len(group)
        })
    
    if not dimension_summary:
        return [types.TextContent(type="text", text=f"❌ 科目 {subject_code} 没有符合条件的核算维度记录（所有维度余额均为零）")]
    
    # 排序
    if sort_by == "ending_balance":
        dimension_summary.sort(key=lambda x: abs(x["ending_balance"]), reverse=True)
    elif sort_by == "total_debit":
        dimension_summary.sort(key=lambda x: x["total_debit"], reverse=True)
    elif sort_by == "total_credit":
        dimension_summary.sort(key=lambda x: x["total_credit"], reverse=True)
    elif sort_by == "dimension_name":
        dimension_summary.sort(key=lambda x: x["dimension_name"])
    
    # 限制返回数量
    dimension_summary = dimension_summary[:limit]
    
    # 格式化输出
    output_lines = [f"# 核算维度明细查询: 科目 {subject_code}\n"]
    output_lines.append(f"**找到维度数量**: {len(dimension_summary)}")
    output_lines.append(f"**排序方式**: {sort_by}")
    output_lines.append("")
    
    for i, dim in enumerate(dimension_summary, 1):
        balance_sign = "借" if dim["ending_balance"] > 0 else "贷"
        balance_abs = abs(dim["ending_balance"])
        
        output_lines.append(f"## {i}. {dim['dimension_name']}")
        output_lines.append(f"**期末余额**: {format_amount(balance_abs)} ({balance_sign})")
        output_lines.append(f"**本年借方**: {format_amount(dim['total_debit'])}")
        output_lines.append(f"**本年贷方**: {format_amount(dim['total_credit'])}")
        output_lines.append(f"**记录数量**: {dim['record_count']}")
        output_lines.append("")
    
    # 提供使用建议
    output_lines.append("---")
    output_lines.append("💡 **使用建议**:")
    output_lines.append("- 使用 dimension_name 参数筛选特定类型的维度（如：供应商、客户）")
    output_lines.append("- 使用 sort_by 参数改变排序方式")
    output_lines.append("- 设置 show_zero_balance=true 显示余额为零的维度")
    output_lines.append("- 复制维度名称用于精确查询")
    
    return [types.TextContent(type="text", text="\n".join(output_lines))]

async def main():
    # 在服务器启动时预加载数据
    try:
        load_data()
        print("财务数据加载成功", file=sys.stderr)
        print(f"Python executable: {sys.executable}", file=sys.stderr)
        print(f"Pandas version: {pd.__version__}", file=sys.stderr)
    except Exception as e:
        print(f"数据加载失败: {e}", file=sys.stderr)
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="financial-data-query",
                server_version="1.0.0",
                capabilities=types.ServerCapabilities(
                    tools=types.ToolsCapability(listChanged=True),
                    experimental=None,
                    logging=None,
                    prompts=None,
                    resources=None,
                    completions=None
                ),
            ),
        )

if __name__ == "__main__":
    import sys
    asyncio.run(main())