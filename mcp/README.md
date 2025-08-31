# 财务数据MCP工具使用指南

## 概述

这是一个专门用于查询和分析format-data/financial目录下财务数据的MCP工具，支持对科目余额表和凭证明细的多维度查询分析。

## 文件结构

```
mcp/
├── financial_data_mcp.py   # MCP服务器主文件
└── README.md               # 使用文档
```

## 安装与配置

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置MCP客户端

在MCP客户端配置文件中添加：

```json
{
  "mcpServers": {
    "financial-data-query": {
      "command": "python",
      "args": ["D:/Audit-p/mcp/financial_data_mcp.py"],
      "cwd": "D:/Audit-p"
    }
  }
}
```

## 可用工具

### 1. query_balance_sheet - 查询科目余额表
查询科目余额表数据，支持多种筛选条件。

**参数：**
- `company`: 公司名称（支持部分匹配）
- `period`: 会计期间
- `subject_code`: 科目编码（支持部分匹配）
- `subject_path`: 科目路径（如：/1002/ 查询银行存款及其子科目）
- `year`: 年份
- `limit`: 返回结果数量限制（默认100）

**示例：**
```
查询银行存款相关科目的余额
query_balance_sheet(subject_code="1002", year=2024)
```

### 2. query_voucher_details - 查询凭证明细
查询凭证明细数据，支持按多种条件筛选。

**参数：**
- `company`: 公司名称
- `subject_code`: 科目编码
- `date_start`: 开始日期 (YYYY-MM-DD)
- `date_end`: 结束日期 (YYYY-MM-DD)
- `voucher_no`: 凭证号
- `amount_min`: 最小金额
- `amount_max`: 最大金额
- `limit`: 返回结果数量限制（默认100）

**示例：**
```
查询2024年1月银行存款相关凭证
query_voucher_details(subject_code="1002", date_start="2024-01-01", date_end="2024-01-31")
```

### 3. analyze_subject_hierarchy - 科目层级分析
分析指定科目的层级结构，显示所有子科目和汇总信息。

**参数：**
- `subject_code`: 父级科目编码（必需）
- `company`: 公司名称
- `year`: 年份

**示例：**
```
分析银行存款科目的层级结构
analyze_subject_hierarchy(subject_code="1002")
```

### 4. get_financial_summary - 财务数据汇总
获取财务数据的汇总统计信息。

**参数：**
- `company`: 公司名称
- `year`: 年份
- `summary_type`: 汇总类型（balance/voucher/both，默认both）

**示例：**
```
获取2024年财务数据汇总
get_financial_summary(year=2024, summary_type="both")
```

### 5. search_transactions - 交易记录搜索
在凭证摘要中搜索特定关键词的交易记录。

**参数：**
- `keyword`: 搜索关键词（必需）
- `company`: 公司名称
- `date_start`: 开始日期
- `date_end`: 结束日期
- `limit`: 返回结果数量限制（默认50）

**示例：**
```
搜索包含"货款"的交易记录
search_transactions(keyword="货款")
```

## 数据说明

### 科目余额表 (final_enhanced_balance.csv)
- 数据规模：8,666行 × 17列
- 时间覆盖：2023年-2025年7月
- 支持科目层级查询和核算维度分析

### 凭证明细表 (final_voucher_detail.csv)
- 数据规模：52,170行 × 27列
- 时间覆盖：2024年1月-2025年6月
- 包含完整的凭证分录信息

## 使用技巧

1. **层级查询**：使用`subject_path`参数进行科目层级查询，如`/1002/`查询银行存款及其所有子科目

2. **关联分析**：结合余额表和凭证明细进行分析，通过科目编码关联

3. **数据筛选**：支持多条件组合筛选，提高查询精度

4. **结果限制**：合理设置`limit`参数避免返回过多数据

## 故障排除

1. **文件不存在错误**：确保format-data/financial目录下有相应的CSV文件
2. **内存不足**：如果数据量大，考虑增加筛选条件减少结果集
3. **编码问题**：确保CSV文件使用UTF-8编码

## 版本信息

- 版本：1.0.0
- 支持的数据格式：CSV
- Python版本要求：3.8+