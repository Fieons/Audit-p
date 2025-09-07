# 财务数据MCP工具使用指南

## 📋 概述

这是一个功能强大的财务数据查询MCP工具，专门用于查询和分析 `format-data/financial` 目录下的财务数据。支持对科目余额表和凭证明细进行多维度、智能化的查询分析，内置会计逻辑验证和业务类型识别功能。

## 🏗️ 系统架构

```
项目根目录/
├── mcp/
│   ├── financial_data_mcp.py   # MCP服务器核心实现
│   ├── run_financial_mcp.py    # MCP服务器启动包装脚本
│   └── README.md               # 详细使用文档
├── .mcp.json                   # MCP客户端标准配置文件
├── format-data/financial/      # 财务数据文件目录
│   ├── final_enhanced_balance.csv
│   └── final_voucher_detail.csv
└── venv/                       # Python虚拟环境（可选）
```

## 🚀 快速开始

### 1. 环境准备

确保已安装Python 3.8+和必要的依赖：

```bash
# 激活虚拟环境（如果使用）
# source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. MCP配置与运行逻辑

#### 配置架构说明

项目采用标准化的MCP配置架构：

1. **`.mcp.json`** - 标准MCP客户端配置文件
   - 位于项目根目录
   - 被大多数MCP客户端自动识别
   - 使用相对路径配置，确保项目可移植性

2. **`run_financial_mcp.py`** - 智能启动包装脚本
   - 自动检测并使用虚拟环境中的Python解释器
   - 提供跨平台支持（Windows/Linux/macOS）
   - 确保正确的工作目录设置

3. **`financial_data_mcp.py`** - MCP服务器核心实现
   - 包含所有财务数据查询工具
   - 处理MCP协议通信
   - 实现数据加载和查询逻辑

#### 标准配置内容

项目根目录的 `.mcp.json` 文件包含：

```json
{
  "mcpServers": {
    "financial-data-query": {
      "command": "python",
      "args": ["mcp/run_financial_mcp.py"],
      "cwd": "."
    }
  }
}
```

#### 运行时逻辑流程

```
MCP客户端 → 读取.mcp.json → 执行python mcp/run_financial_mcp.py
                      ↓
        run_financial_mcp.py 执行流程：
        1. 检测虚拟环境 → 优先使用venv中的Python
        2. 设置工作目录 → 项目根目录
        3. 启动financial_data_mcp.py
                      ↓
    financial_data_mcp.py 加载流程：
        1. 加载财务数据文件
        2. 初始化MCP服务器
        3. 等待客户端请求
```

### 3. 验证安装

启动MCP客户端后，尝试执行以下命令验证连接：

```
get_financial_summary()
```

## 🛠️ 可用工具详解

### 1. query_balance_sheet - 查询科目余额表

**功能**: 查询科目余额表数据，支持多种筛选条件和会计逻辑验证

**参数说明:**
| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `company` | string | 否 | 公司名称（支持部分匹配） | "碳元科技" |
| `period` | string | 否 | 会计期间 | "2024年12月" |
| `subject_code` | string | 否 | 科目编码（支持部分匹配和层级查询） | "1002"（银行存款） |
| `subject_path` | string | 否 | 科目路径查询 | "/1002/"（银行存款及所有子科目） |
| `dimension_name` | string | 否 | 核算维度名称 | "供应商A" |
| `subject_name_path` | string | 否 | 科目名称路径 | "/银行存款/" |
| `year` | integer | 否 | 年份（2000-2050） | 2024 |
| `limit` | integer | 否 | 返回结果数量限制 | 100 |
| `include_dimensions` | boolean | 否 | 是否包含核算维度明细 | true |

**使用示例:**
```
# 查询银行存款科目余额
query_balance_sheet(subject_code="1002", year=2024)

# 查询应付账款相关科目（包含所有子科目）
query_balance_sheet(subject_path="/2202/", company="碳元")

# 查询特定核算维度的余额
query_balance_sheet(subject_code="2202", dimension_name="供应商A")
```

### 2. query_voucher_details - 查询凭证明细

**功能**: 查询凭证明细数据，支持精确筛选和业务类型识别

**参数说明:**
| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `company` | string | 否 | 公司名称 | "碳元科技" |
| `subject_code` | string | 否 | 科目编码 | "1002" |
| `date_start` | string | 否 | 开始日期（YYYY-MM-DD） | "2024-01-01" |
| `date_end` | string | 否 | 结束日期（YYYY-MM-DD） | "2024-12-31" |
| `voucher_no` | string | 否 | 凭证号 | "记-1001" |
| `amount_min` | number | 否 | 最小金额（≥0） | 1000 |
| `amount_max` | number | 否 | 最大金额 | 100000 |
| `limit` | integer | 否 | 返回结果数量限制 | 100 |

### 3. analyze_subject_hierarchy - 科目层级分析

**功能**: 分析指定科目的完整层级结构，显示所有子科目和汇总信息

**参数说明:**
| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `subject_code` | string | 是 | 父级科目编码 | "1002" |
| `company` | string | 否 | 公司名称 | "碳元科技" |
| `year` | integer | 否 | 年份 | 2024 |

### 4. get_financial_summary - 财务数据汇总

**功能**: 获取财务数据的整体汇总统计信息

**参数说明:**
| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `company` | string | 否 | 公司名称 | "碳元科技" |
| `year` | integer | 否 | 年份 | 2024 |
| `summary_type` | string | 否 | 汇总类型：balance/voucher/both | "both" |

### 5. search_transactions - 交易记录搜索

**功能**: 在凭证摘要中智能搜索特定关键词的交易记录

**参数说明:**
| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `keyword` | string | 是 | 搜索关键词 | "货款" |
| `company` | string | 否 | 公司名称 | "碳元科技" |
| `date_start` | string | 否 | 开始日期 | "2024-01-01" |
| `date_end` | string | 否 | 结束日期 | "2024-12-31" |
| `limit` | integer | 否 | 返回结果数量限制 | 50 |

### 6. validate_data_consistency - 数据一致性验证

**功能**: 验证科目余额表和凭证明细数据的一致性

**参数说明:**
| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `subject_code` | string | 是 | 科目编码 | "1002" |
| `company` | string | 否 | 公司名称 | "碳元科技" |
| `year` | integer | 否 | 年份 | 2024 |

### 7. find_subject_by_name - 科目名称查找

**功能**: 通过科目名称智能查找对应的科目编码和层级信息

**参数说明:**
| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `subject_name` | string | 是 | 科目名称 | "其他应付款" |
| `company` | string | 否 | 公司名称 | "碳元科技" |
| `fuzzy_match` | boolean | 否 | 是否启用模糊匹配 | true |
| `limit` | integer | 否 | 返回结果数量限制 | 20 |

### 8. query_dimension_details - 核算维度明细查询

**功能**: 查询指定科目的核算维度明细信息

**参数说明:**
| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `subject_code` | string | 是 | 科目编码 | "2202" |
| `company` | string | 否 | 公司名称 | "碳元科技" |
| `year` | integer | 否 | 年份 | 2024 |
| `dimension_type` | string | 否 | 维度类型筛选 | "供应商" |
| `sort_by` | string | 否 | 排序方式 | "ending_balance" |
| `limit` | integer | 否 | 返回结果数量限制 | 100 |
| `show_zero_balance` | boolean | 否 | 是否显示零余额维度 | false |

## 📊 数据源说明

### 科目余额表 (final_enhanced_balance.csv)
- **数据规模**: 8,666行 × 17列
- **时间覆盖**: 2023年 - 2025年7月
- **主要字段**: 公司、期间、年份、科目编码、科目名称、期初余额、本年累计、期末余额等

### 凭证明细表 (final_voucher_detail.csv)  
- **数据规模**: 52,170行 × 27列
- **时间覆盖**: 2024年1月 - 2025年6月
- **主要字段**: 公司、日期、凭证字、凭证号、摘要、科目编码、科目全名、借方金额、贷方金额等

## 🔧 技术支持

### 版本信息
- **MCP服务器版本**: 1.0.0
- **Python要求**: 3.8+
- **数据格式**: CSV
- **更新时间**: 2025-09-07

### 故障排除

1. **确保数据文件存在**: 检查 `format-data/financial/` 目录下的CSV文件
2. **验证虚拟环境**: `run_financial_mcp.py` 会自动检测venv目录
3. **检查文件编码**: 确保CSV文件使用UTF-8编码
4. **查看日志信息**: MCP服务器会输出加载状态信息

### 获取帮助
如果遇到问题，可以：
1. 使用 `get_financial_summary()` 查看数据可用性
2. 检查MCP客户端连接状态
3. 验证数据文件是否存在且格式正确
4. 查看具体的错误信息提示

---

💡 **提示**: 本工具采用标准化MCP配置，支持自动虚拟环境检测和跨平台运行，大大简化了部署和使用流程。