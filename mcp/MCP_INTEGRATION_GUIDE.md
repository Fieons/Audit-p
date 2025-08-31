# MCP 财务数据查询工具 - 完整集成指南

## 📋 概述

本项目提供了一个完整的 MCP (Model Context Protocol) 服务器，用于查询和分析财务数据。支持对科目余额表和凭证明细的多维度查询分析。

## 📁 文件结构

```
D:\Audit-p\
├── .mcp.json                     # MCP 服务器配置文件
├── run_financial_mcp.py          # 跨平台启动包装脚本
├── mcp/                          # MCP 服务器目录
│   ├── financial_data_mcp.py     # MCP 服务器主文件
│   ├── README.md                 # 详细使用文档
│   ├── test_mcp_server.py        # MCP 服务器测试脚本
│   ├── test_functionality.py     # 功能测试脚本
│   ├── start_financial_mcp.bat   # Windows 启动脚本
│   ├── start_financial_mcp.sh    # Unix/Linux 启动脚本
│   └── __pycache__/              # Python 缓存目录
└── format-data/financial/        # 财务数据文件
    ├── final_enhanced_balance.csv    # 科目余额表
    └── final_voucher_detail.csv      # 凭证明细表
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 确保虚拟环境已创建并激活
python -m venv venv

# Windows
venv\Scripts\activate

# Unix/Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置 MCP 客户端

在 MCP 客户端配置文件中添加以下配置：

```json
{
  "mcpServers": {
    "financial-data-query": {
      "command": "python",
      "args": ["run_financial_mcp.py"],
      "cwd": ".",
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

### 3. 启动 MCP 服务器

有多种启动方式：

**方式 1: 使用包装脚本（推荐）**
```bash
python run_financial_mcp.py
```

**方式 2: 直接运行 MCP 服务器**
```bash
# Windows
venv\Scripts\python.exe mcp\financial_data_mcp.py

# Unix/Linux/Mac
venv/bin/python mcp/financial_data_mcp.py
```

**方式 3: 使用平台特定脚本**
```bash
# Windows
mcp\start_financial_mcp.bat

# Unix/Linux/Mac
bash mcp/start_financial_mcp.sh
```

## 🛠️ 可用工具

### 1. query_balance_sheet - 查询科目余额表
查询科目余额表数据，支持多种筛选条件。

**参数：**
- `company`: 公司名称（支持部分匹配）
- `period`: 会计期间
- `subject_code`: 科目编码（支持部分匹配）
- `subject_path`: 科目路径（如：/1002/ 查询银行存款及其子科目）
- `year`: 年份
- `limit`: 返回结果数量限制（默认100）

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

### 3. analyze_subject_hierarchy - 科目层级分析
分析指定科目的层级结构，显示所有子科目和汇总信息。

**参数：**
- `subject_code`: 父级科目编码（必需）
- `company`: 公司名称
- `year`: 年份

### 4. get_financial_summary - 财务数据汇总
获取财务数据的汇总统计信息。

**参数：**
- `company`: 公司名称
- `year`: 年份
- `summary_type`: 汇总类型（balance/voucher/both，默认both）

### 5. search_transactions - 交易记录搜索
在凭证摘要中搜索特定关键词的交易记录。

**参数：**
- `keyword`: 搜索关键词（必需）
- `company`: 公司名称
- `date_start`: 开始日期
- `date_end`: 结束日期
- `limit`: 返回结果数量限制（默认50）

## 📊 数据说明

### 科目余额表 (final_enhanced_balance.csv)
- 数据规模：8,666行 × 17列
- 时间覆盖：2023年-2025年7月
- 支持科目层级查询和核算维度分析

### 凭证明细表 (final_voucher_detail.csv)
- 数据规模：52,170行 × 27列
- 时间覆盖：2024年1月-2025年6月
- 包含完整的凭证分录信息

## 🧪 测试与验证

### 运行完整测试套件

```bash
# 测试数据加载和基本功能
python mcp/test_mcp_server.py

# 测试财务查询功能
python mcp/test_functionality.py
```

### 测试输出示例

```
MCP Financial Data Server Test
==================================================
Checking data files...
Balance file exists: True
Voucher file exists: True

Testing data loading...
Balance data shape: (8666, 17)
Balance columns: ['公司', '期间', '年份', '科目编码', '科目名称', ...]

TEST RESULTS:
Data Test: PASS
Functionality Test: PASS
Connection Test: PASS

All tests passed! MCP server is ready for use.
```

## 🔧 故障排除

### 常见问题

1. **文件不存在错误**
   - 确保 `format-data/financial/` 目录下有相应的 CSV 文件
   - 检查文件路径和权限

2. **依赖安装问题**
   - 确保虚拟环境已激活：`venv\Scripts\activate` (Windows) 或 `source venv/bin/activate` (Unix)
   - 重新安装依赖：`pip install -r requirements.txt`

3. **内存不足**
   - 如果数据量大，增加筛选条件减少结果集
   - 合理设置 `limit` 参数

4. **编码问题**
   - 确保 CSV 文件使用 UTF-8 编码

### 调试模式

启用详细日志输出：

```bash
# 设置环境变量启用调试
set MCP_DEBUG=1
python run_financial_mcp.py
```

## 🌐 支持的 MCP 客户端

- Claude Desktop App
- VS Code with MCP extension
- Cursor IDE
- 其他 MCP 兼容工具

## 📝 开发说明

### 代码结构

- `financial_data_mcp.py`: 主服务器文件，包含所有工具实现
- 使用 pandas 进行数据处理和筛选
- 支持异步操作和实时数据加载

### 扩展开发

要添加新工具，在 `financial_data_mcp.py` 中：

1. 在 `handle_list_tools()` 中添加工具定义
2. 在 `handle_call_tool()` 中添加工具调用处理
3. 实现对应的异步处理函数

### 性能优化

- 数据在启动时预加载到内存
- 支持数据筛选和分页
- 使用 pandas 进行高效数据处理

## 📞 支持

如有问题，请检查：
1. 数据文件是否存在且格式正确
2. 虚拟环境配置是否正确
3. MCP 客户端配置是否正确

## 📄 许可证

本项目基于 MIT 许可证开源。

---

**版本**: 1.0.0  
**最后更新**: 2025-08-31  
**Python 要求**: 3.8+