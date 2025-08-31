# Financial Data Cleaning and Validation Scripts

本目录包含财务数据清洗和验证相关的Python脚本，主要用于处理科目余额表和凭证明细表数据。

## 脚本功能说明

### 1. financial_validation.py
**财务数据验证器**

主要功能：
- **会计恒等式验证**: 验证不同科目类型的会计恒等式平衡
- **年度连续性验证**: 验证同一公司上年的期末余额等于当年的期初余额
- **层级数据正确性验证**: 验证下级科目汇总数等于上级科目余额和发生额，支持借贷抵消后的净额验证
- **凭证明细勾稽关系验证**: 验证凭证明细表与科目余额表的发生额勾稽关系

验证逻辑特点：
- 支持资产类、负债类、所有者权益类、收入类、费用类科目的不同验证规则
- 层级验证考虑父级科目汇总时借贷双方金额抵消后只保留净余额的情况
- 生成详细的验证报告和错误CSV文件

### 2. adjust_opening_balance.py
**期初余额调整脚本**

主要功能：
- 处理科目余额表的期初余额数据
- 确保期初余额的准确性和连续性
- 为后续的数据验证和处理提供基础数据支持

## 数据验证逻辑

### 层级验证改进
在`validate_hierarchy_correctness`函数中，增加了对借贷抵消情况的处理：

- **资产类和费用类科目**: 验证借方-贷方净额是否相等
- **负债类、权益类和收入类科目**: 验证贷方-借方净额是否相等  
- **未知类型科目**: 保持原有的逐项比较方式

### 验证报告输出
验证完成后会生成：
- `validation_report.txt`: 文本格式的验证结果摘要
- `validation_errors.csv`: CSV格式的详细错误记录

## 使用说明

1. 确保数据文件位于`/home/Fieons/Audit-p/format-data/financial/`目录
2. 运行完整验证: `python financial_validation.py`
3. 查看生成的验证报告和错误文件

## 数据要求

输入文件：
- `final_enhanced_balance.csv`: 增强版科目余额表
- `final_voucher_detail.csv`: 凭证明细表

输出文件：
- `validation_report.txt`: 验证结果报告
- `validation_errors.csv`: 详细错误记录