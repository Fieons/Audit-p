#!/usr/bin/env python3
"""
财务数据验证脚本
对科目余额表和凭证明细表进行数据验证
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinancialDataValidator:
    def __init__(self, data_dir: str = "/home/Fieons/Audit-p/format-data/financial"):
        """初始化验证器"""
        self.data_dir = Path(data_dir)
        self.balance_df = None
        self.voucher_df = None
        self.validation_results = {}
        
    def load_data(self):
        """加载数据文件"""
        try:
            balance_file = self.data_dir / "final_enhanced_balance.csv"
            voucher_file = self.data_dir / "final_voucher_detail.csv"
            
            logger.info(f"正在加载科目余额表: {balance_file}")
            self.balance_df = pd.read_csv(balance_file, encoding='utf-8')
            
            logger.info(f"正在加载凭证明细表: {voucher_file}")
            self.voucher_df = pd.read_csv(voucher_file, encoding='utf-8')
            
            logger.info(f"科目余额表形状: {self.balance_df.shape}")
            logger.info(f"凭证明细表形状: {self.voucher_df.shape}")
            
            # 数据预处理
            self._preprocess_data()
            
        except Exception as e:
            logger.error(f"数据加载失败: {e}")
            raise
    
    def _preprocess_data(self):
        """数据预处理"""
        # 确保金额字段为数值类型
        amount_columns = ['期初余额借方', '期初余额贷方', '本年累计借方', '本年累计贷方', 
                         '期末余额借方', '期末余额贷方']
        
        for col in amount_columns:
            self.balance_df[col] = pd.to_numeric(self.balance_df[col], errors='coerce').fillna(0)
        
        # 处理凭证明细表的金额字段
        self.voucher_df['借方金额'] = pd.to_numeric(self.voucher_df['借方金额'], errors='coerce').fillna(0)
        self.voucher_df['贷方金额'] = pd.to_numeric(self.voucher_df['贷方金额'], errors='coerce').fillna(0)
        
        # 提取年份信息
        self.balance_df['年份'] = self.balance_df['期间'].astype(str).str.extract(r'(\d{4})')[0].astype(float).astype(int)
        
        # 为凭证明细表添加期间字段（从日期字段提取）
        self.voucher_df['日期'] = pd.to_datetime(self.voucher_df['日期'], errors='coerce')
        self.voucher_df['年份'] = self.voucher_df['日期'].dt.year
        self.voucher_df['月份'] = self.voucher_df['日期'].dt.month
    
    def _get_account_type(self, subject_code: str) -> str:
        """
        根据科目编码判断科目类型
        中国会计准则科目编码规则:
        1xxx: 资产类
        2xxx: 负债类  
        3xxx: 所有者权益类
        4xxx: 收入类
        5xxx: 费用类
        6xxx: 损益类
        """
        code = str(subject_code).split('.')[0]  # 取主科目编码
        if code.startswith('1'):
            return 'asset'
        elif code.startswith('2'):
            return 'liability'
        elif code.startswith('3'):
            return 'equity'
        elif code.startswith('4'):
            return 'income'
        elif code.startswith('5') or code.startswith('6'):
            return 'expense'
        else:
            return 'unknown'
    
    def validate_accounting_equation(self) -> Dict:
        """
        验证1: 会计恒等式平衡验证
        根据不同科目类型使用不同的验证公式:
        - 资产类: 期初借方 - 期初贷方 + 本年累计借方 - 本年累计贷方 = 期末借方 - 期末贷方
        - 负债类: 期初贷方 - 期初借方 + 本年累计贷方 - 本年累计借方 = 期末贷方 - 期末借方
        - 所有者权益类: 期初贷方 - 期初借方 + 本年累计贷方 - 本年累计借方 = 期末贷方 - 期末借方
        - 收入类: 本年累计贷方 - 本年累计借方 = 期末贷方 - 期末借方 (期初应为0)
        - 费用类: 本年累计借方 - 本年累计贷方 = 期末借方 - 期末贷方 (期初应为0)
        """
        logger.info("开始验证会计恒等式平衡...")
        
        results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
        for idx, row in self.balance_df.iterrows():
            # 包括核算维度行也需要验证
            account_type = self._get_account_type(row['科目编码'])
            tolerance = 0.01
            
            # 根据科目类型使用不同的验证逻辑
            if account_type == 'asset':
                # 资产类: 借方增加，贷方减少
                opening_net = row['期初余额借方'] - row['期初余额贷方']
                period_net = row['本年累计借方'] - row['本年累计贷方']
                closing_net = row['期末余额借方'] - row['期末余额贷方']
                expected_closing = opening_net + period_net
                
            elif account_type in ['liability', 'equity']:
                # 负债类和权益类: 贷方增加，借方减少
                opening_net = row['期初余额贷方'] - row['期初余额借方']
                period_net = row['本年累计贷方'] - row['本年累计借方']
                closing_net = row['期末余额贷方'] - row['期末余额借方']
                expected_closing = opening_net + period_net
                
            elif account_type == 'income':
                # 收入类: 贷方增加，期初一般为0
                opening_net = row['期初余额贷方'] - row['期初余额借方']
                period_net = row['本年累计贷方'] - row['本年累计借方']
                closing_net = row['期末余额贷方'] - row['期末余额借方']
                expected_closing = opening_net + period_net
                
            elif account_type == 'expense':
                # 费用类: 借方增加，期初一般为0
                opening_net = row['期初余额借方'] - row['期初余额贷方']
                period_net = row['本年累计借方'] - row['本年累计贷方']
                closing_net = row['期末余额借方'] - row['期末余额贷方']
                expected_closing = opening_net + period_net
                
            else:
                # 未知类型，跳过验证
                continue
            
            # 验证恒等式
            if abs(closing_net - expected_closing) > tolerance:
                dimension_info = f" 核算维度: {row['核算维度名称']}" if row['is_dimension_row'] else ""
                error_msg = (
                    f"科目 {row['科目编码']} ({row['科目名称']}){dimension_info} [{account_type}类] 会计恒等式不平衡: "
                    f"期初净额({opening_net:.2f}) + 发生净额({period_net:.2f}) = {expected_closing:.2f}, "
                    f"但期末净额为 {closing_net:.2f}, 差异: {closing_net - expected_closing:.2f}"
                )
                results['errors'].append({
                    'type': 'accounting_equation',
                    'subject_code': row['科目编码'],
                    'subject_name': row['科目名称'],
                    'dimension_name': row['核算维度名称'] if row['is_dimension_row'] else None,
                    'account_type': account_type,
                    'company': row['公司'],
                    'period': row['期间'],
                    'opening_net': opening_net,
                    'period_net': period_net,
                    'closing_net': closing_net,
                    'expected_closing': expected_closing,
                    'difference': closing_net - expected_closing,
                    'message': error_msg
                })
                results['failed'] += 1
            else:
                results['passed'] += 1
        
        logger.info(f"会计恒等式验证完成: 通过 {results['passed']}, 失败 {results['failed']}")
        self.validation_results['accounting_equation'] = results
        return results
    
    def validate_year_continuity(self) -> Dict:
        """
        验证2: 年度连续性验证
        同一公司上年的期末余额等于当年的期初余额
        """
        logger.info("开始验证年度连续性...")
        
        results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
        # 按公司和科目分组
        grouped = self.balance_df.groupby(['公司', '科目编码'])
        
        for (company, subject_code), group in grouped:
            # 按年份排序
            group = group.sort_values('年份')
            
            if len(group) < 2:
                continue  # 需要至少两年数据
            
            for i in range(1, len(group)):
                prev_year = group.iloc[i-1]
                curr_year = group.iloc[i]
                
                # 检查是否连续年份
                if curr_year['年份'] != prev_year['年份'] + 1:
                    continue
                
                # 验证: 上年的期末余额 = 当年的期初余额
                prev_closing_debit = prev_year['期末余额借方']
                prev_closing_credit = prev_year['期末余额贷方']
                curr_opening_debit = curr_year['期初余额借方']
                curr_opening_credit = curr_year['期初余额贷方']
                
                tolerance = 0.01
                debit_match = abs(prev_closing_debit - curr_opening_debit) <= tolerance
                credit_match = abs(prev_closing_credit - curr_opening_credit) <= tolerance
                
                if not (debit_match and credit_match):
                    error_msg = (
                        f"科目 {subject_code} 年度连续性错误: "
                        f"{prev_year['年份']}年末余额(借{prev_closing_debit:.2f}/贷{prev_closing_credit:.2f}) "
                        f"≠ {curr_year['年份']}年初余额(借{curr_opening_debit:.2f}/贷{curr_opening_credit:.2f})"
                    )
                    results['errors'].append({
                        'type': 'year_continuity',
                        'subject_code': subject_code,
                        'company': company,
                        'prev_year': prev_year['年份'],
                        'curr_year': curr_year['年份'],
                        'prev_closing_debit': prev_closing_debit,
                        'prev_closing_credit': prev_closing_credit,
                        'curr_opening_debit': curr_opening_debit,
                        'curr_opening_credit': curr_opening_credit,
                        'message': error_msg
                    })
                    results['failed'] += 1
                else:
                    results['passed'] += 1
        
        logger.info(f"年度连续性验证完成: 通过 {results['passed']}, 失败 {results['failed']}")
        self.validation_results['year_continuity'] = results
        return results
    
    def validate_hierarchy_correctness(self) -> Dict:
        """
        验证3: 层级数据正确性验证
        下级科目汇总数等于上级科目余额和发生额
        考虑父级科目汇总时，借贷双方金额可能抵消后只保留净余额
        """
        logger.info("开始验证层级数据正确性...")
        
        results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
        # 获取所有非核算维度行
        non_dimension_df = self.balance_df[~self.balance_df['is_dimension_row']]
        
        # 按公司、期间分组验证
        grouped = non_dimension_df.groupby(['公司', '期间'])
        
        for (company, period), period_group in grouped:
            # 构建科目层级树
            subject_tree = self._build_subject_tree(period_group)
            
            # 验证每个父科目
            for parent_code, children in subject_tree.items():
                if parent_code not in period_group['科目编码'].values:
                    continue  # 跳过不存在的父科目
                
                parent_row = period_group[period_group['科目编码'] == parent_code].iloc[0]
                parent_account_type = self._get_account_type(parent_code)
                
                # 汇总子科目数据
                child_debit_open = sum(child['期初余额借方'] for child in children)
                child_credit_open = sum(child['期初余额贷方'] for child in children)
                child_debit_current = sum(child['本年累计借方'] for child in children)
                child_credit_current = sum(child['本年累计贷方'] for child in children)
                child_debit_close = sum(child['期末余额借方'] for child in children)
                child_credit_close = sum(child['期末余额贷方'] for child in children)
                
                tolerance = 0.01
                
                # 根据科目类型决定验证策略
                if parent_account_type in ['asset', 'expense']:
                    # 资产类和费用类科目：借方为正常余额方向
                    # 验证净额是否相等（允许借贷抵消后只显示净余额）
                    parent_net_open = parent_row['期初余额借方'] - parent_row['期初余额贷方']
                    child_net_open = child_debit_open - child_credit_open
                    
                    parent_net_current = parent_row['本年累计借方'] - parent_row['本年累计贷方']
                    child_net_current = child_debit_current - child_credit_current
                    
                    parent_net_close = parent_row['期末余额借方'] - parent_row['期末余额贷方']
                    child_net_close = child_debit_close - child_credit_close
                    
                    checks = [
                        ('期初净额', parent_net_open, child_net_open),
                        ('本年累计净额', parent_net_current, child_net_current),
                        ('期末净额', parent_net_close, child_net_close)
                    ]
                    
                elif parent_account_type in ['liability', 'equity', 'income']:
                    # 负债类、所有者权益类、收入类科目：贷方为正常余额方向
                    # 验证净额是否相等（允许借贷抵消后只显示净余额）
                    parent_net_open = parent_row['期初余额贷方'] - parent_row['期初余额借方']
                    child_net_open = child_credit_open - child_debit_open
                    
                    parent_net_current = parent_row['本年累计贷方'] - parent_row['本年累计借方']
                    child_net_current = child_credit_current - child_debit_current
                    
                    parent_net_close = parent_row['期末余额贷方'] - parent_row['期末余额借方']
                    child_net_close = child_credit_close - child_debit_close
                    
                    checks = [
                        ('期初净额', parent_net_open, child_net_open),
                        ('本年累计净额', parent_net_current, child_net_current),
                        ('期末净额', parent_net_close, child_net_close)
                    ]
                else:
                    # 未知类型科目，使用原来的逐项比较方式
                    checks = [
                        ('期初借方', parent_row['期初余额借方'], child_debit_open),
                        ('期初贷方', parent_row['期初余额贷方'], child_credit_open),
                        ('本年累计借方', parent_row['本年累计借方'], child_debit_current),
                        ('本年累计贷方', parent_row['本年累计贷方'], child_credit_current),
                        ('期末借方', parent_row['期末余额借方'], child_debit_close),
                        ('期末贷方', parent_row['期末余额贷方'], child_credit_close)
                    ]
                
                # 执行验证检查
                for field, parent_val, child_sum in checks:
                    if abs(parent_val - child_sum) > tolerance:
                        error_msg = (
                            f"层级汇总错误: 科目 {parent_code} ({parent_account_type}类) {field} "
                            f"父科目值({parent_val:.2f}) ≠ 子科目汇总({child_sum:.2f}), "
                            f"差异: {parent_val - child_sum:.2f}"
                        )
                        results['errors'].append({
                            'type': 'hierarchy_correctness',
                            'parent_subject': parent_code,
                            'account_type': parent_account_type,
                            'company': company,
                            'period': period,
                            'field': field,
                            'parent_value': parent_val,
                            'child_sum': child_sum,
                            'difference': parent_val - child_sum,
                            'message': error_msg
                        })
                        results['failed'] += 1
                    else:
                        results['passed'] += 1
        
        logger.info(f"层级数据正确性验证完成: 通过 {results['passed']}, 失败 {results['failed']}")
        self.validation_results['hierarchy_correctness'] = results
        return results
    
    def _build_subject_tree(self, df: pd.DataFrame) -> Dict:
        """构建科目层级树"""
        tree = {}
        
        for _, row in df.iterrows():
            subject_code = str(row['科目编码'])
            
            # 找出所有可能的父科目
            parent_candidates = []
            parts = subject_code.split('.')
            
            for i in range(1, len(parts)):
                parent_code = '.'.join(parts[:i])
                if parent_code in df['科目编码'].astype(str).values:
                    parent_candidates.append(parent_code)
            
            # 取最直接的父科目（编码最长的，即最接近的上级科目）
            if parent_candidates:
                parent_code = max(parent_candidates, key=len)
                if parent_code not in tree:
                    tree[parent_code] = []
                tree[parent_code].append(row)
        
        return tree
    
    def validate_voucher_reconciliation(self) -> Dict:
        """
        验证4: 凭证明细表与科目余额表勾稽关系验证
        从凭证明细表出发，验证科目余额表的发生额是否能勾稽得上
        考虑层级关系：汇总性科目不在凭证明细中出现，只有末级科目出现
        """
        logger.info("开始验证凭证明细勾稽关系...")
        
        results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
        # 按公司、会计年度、科目编码分组汇总凭证明细
        voucher_summary = self.voucher_df.groupby(['公司', '会计年度', '科目编码']).agg({
            '借方金额': 'sum',
            '贷方金额': 'sum'
        }).reset_index()
        voucher_summary['会计年度'] = voucher_summary['会计年度'].astype(str).str.replace(',', '').astype(float).astype(int)
        
        # 获取凭证明细中存在的科目列表
        voucher_subjects = set(voucher_summary['科目编码'].astype(str))
        logger.info(f"凭证明细中存在 {len(voucher_subjects)} 个科目")
        
        # 筛选科目余额表中在凭证明细中存在的科目
        balance_filtered = self.balance_df[
            self.balance_df['科目编码'].astype(str).isin(voucher_subjects)
        ].copy()
        
        logger.info(f"科目余额表中匹配到 {len(balance_filtered)} 条记录")
        
        # 合并凭证明细汇总和科目余额表
        merged_df = pd.merge(
            voucher_summary,
            balance_filtered,
            on=['公司', '科目编码'],
            how='inner',
            suffixes=('_voucher', '_balance')
        )
        
        # 筛选同年份的数据（只有凭证明细存在的2024年和2025年1-6月数据）
        merged_df = merged_df[
            ((merged_df['会计年度'] == 2024) & (merged_df['年份'] == 2024)) |
            ((merged_df['会计年度'] == 2025) & (merged_df['年份'] == 2025))
        ]
        
        logger.info(f"最终合并得到 {len(merged_df)} 条可验证记录")
        
        for _, row in merged_df.iterrows():
            tolerance = 0.01
            
            # 验证借方和贷方发生额
            debit_diff = abs(row['借方金额'] - row['本年累计借方'])
            credit_diff = abs(row['贷方金额'] - row['本年累计贷方'])
            
            if debit_diff > tolerance or credit_diff > tolerance:
                dimension_info = f" 核算维度: {row['核算维度名称']}" if row['is_dimension_row'] else ""
                error_msg = (
                    f"勾稽关系错误: 科目 {row['科目编码']} ({row['科目名称']}){dimension_info} "
                    f"凭证明细(借{row['借方金额']:.2f}/贷{row['贷方金额']:.2f}) "
                    f"≠ 科目余额(借{row['本年累计借方']:.2f}/贷{row['本年累计贷方']:.2f}) "
                    f"差异(借{row['借方金额'] - row['本年累计借方']:.2f}/贷{row['贷方金额'] - row['本年累计贷方']:.2f})"
                )
                results['errors'].append({
                    'type': 'voucher_reconciliation',
                    'subject_code': row['科目编码'],
                    'subject_name': row['科目名称'],
                    'dimension_name': row['核算维度名称'] if row['is_dimension_row'] else None,
                    'company': row['公司'],
                    'year': row['年份'],
                    'voucher_debit': row['借方金额'],
                    'voucher_credit': row['贷方金额'],
                    'balance_debit': row['本年累计借方'],
                    'balance_credit': row['本年累计贷方'],
                    'debit_difference': row['借方金额'] - row['本年累计借方'],
                    'credit_difference': row['贷方金额'] - row['本年累计贷方'],
                    'message': error_msg
                })
                results['failed'] += 1
            else:
                results['passed'] += 1
        
        logger.info(f"凭证明细勾稽关系验证完成: 通过 {results['passed']}, 失败 {results['failed']}")
        self.validation_results['voucher_reconciliation'] = results
        return results
    
    def _generate_csv_report(self, results: Dict):
        """生成CSV格式的详细错误报告"""
        csv_path = self.data_dir / "validation_errors.csv"
        
        # 收集所有错误
        all_errors = []
        
        for validation_name, result in results['details'].items():
            for error in result['errors']:
                error_record = {
                    '验证类型': validation_name,
                    '错误类型': error.get('type', ''),
                    '科目编码': error.get('subject_code', ''),
                    '科目名称': error.get('subject_name', ''),
                    '核算维度': error.get('dimension_name', ''),
                    '科目类型': error.get('account_type', ''),
                    '公司': error.get('company', ''),
                    '期间': error.get('period', ''),
                    '年份': error.get('year', ''),
                    '错误描述': error.get('message', ''),
                    '差异金额': error.get('difference', ''),
                    '期初净额': error.get('opening_net', ''),
                    '期间净额': error.get('period_net', ''),
                    '期末净额': error.get('closing_net', ''),
                    '预期期末净额': error.get('expected_closing', ''),
                    '凭证借方金额': error.get('voucher_debit', ''),
                    '凭证贷方金额': error.get('voucher_credit', ''),
                    '科目余额借方': error.get('balance_debit', ''),
                    '科目余额贷方': error.get('balance_credit', ''),
                    '借方差异': error.get('debit_difference', ''),
                    '贷方差异': error.get('credit_difference', ''),
                    '上年度': error.get('prev_year', ''),
                    '当年度': error.get('curr_year', ''),
                    '上年期末借方': error.get('prev_closing_debit', ''),
                    '上年期末贷方': error.get('prev_closing_credit', ''),
                    '当年期初借方': error.get('curr_opening_debit', ''),
                    '当年期初贷方': error.get('curr_opening_credit', ''),
                    '父科目': error.get('parent_subject', ''),
                    '验证字段': error.get('field', ''),
                    '父科目值': error.get('parent_value', ''),
                    '子科目汇总': error.get('child_sum', '')
                }
                all_errors.append(error_record)
        
        if all_errors:
            error_df = pd.DataFrame(all_errors)
            # 移除空列
            error_df = error_df.dropna(axis=1, how='all')
            error_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            logger.info(f"CSV错误报告已生成: {csv_path}, 共 {len(all_errors)} 条错误记录")
        else:
            # 如果没有错误，创建一个空的CSV文件
            empty_df = pd.DataFrame([{'结果': '所有验证都通过，没有发现错误'}])
            empty_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            logger.info(f"CSV报告已生成: {csv_path}, 所有验证都通过")
    
    def run_all_validations(self) -> Dict:
        """运行所有验证"""
        logger.info("开始运行所有财务数据验证...")
        
        if self.balance_df is None or self.voucher_df is None:
            self.load_data()
        
        validations = [
            self.validate_accounting_equation,
            self.validate_year_continuity,
            self.validate_hierarchy_correctness,
            self.validate_voucher_reconciliation
        ]
        
        overall_results = {
            'total_passed': 0,
            'total_failed': 0,
            'details': {}
        }
        
        for validation_func in validations:
            try:
                result = validation_func()
                overall_results['total_passed'] += result['passed']
                overall_results['total_failed'] += result['failed']
                overall_results['details'][validation_func.__name__] = result
            except Exception as e:
                logger.error(f"验证 {validation_func.__name__} 失败: {e}")
        
        logger.info(f"所有验证完成: 总计通过 {overall_results['total_passed']}, 失败 {overall_results['total_failed']}")
        
        # 生成详细报告
        self._generate_report(overall_results)
        
        return overall_results
    
    def _generate_report(self, results: Dict):
        """生成验证报告，包括文本报告和CSV详细报告"""
        # 生成文本报告
        report_path = self.data_dir / "validation_report.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("财务数据验证报告\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"验证时间: {pd.Timestamp.now()}\n")
            f.write(f"总计通过: {results['total_passed']}\n")
            f.write(f"总计失败: {results['total_failed']}\n\n")
            
            for validation_name, result in results['details'].items():
                f.write(f"{validation_name}:\n")
                f.write(f"  通过: {result['passed']}, 失败: {result['failed']}\n")
                
                if result['errors']:
                    f.write("  错误详情:\n")
                    for error in result['errors'][:10]:  # 只显示前10个错误
                        f.write(f"    - {error['message']}\n")
                    if len(result['errors']) > 10:
                        f.write(f"    - ... 还有 {len(result['errors']) - 10} 个错误\n")
                f.write("\n")
        
        logger.info(f"验证报告已生成: {report_path}")
        
        # 生成CSV详细报告，列出所有不符合项
        self._generate_csv_report(results)
    
    def _generate_csv_report(self, results: Dict):
        """生成CSV格式的详细错误报告"""
        csv_path = self.data_dir / "validation_errors.csv"
        
        # 收集所有错误
        all_errors = []
        
        for validation_name, result in results['details'].items():
            for error in result['errors']:
                error_record = {
                    '验证类型': validation_name,
                    '错误类型': error.get('type', ''),
                    '科目编码': error.get('subject_code', ''),
                    '科目名称': error.get('subject_name', ''),
                    '核算维度': error.get('dimension_name', ''),
                    '科目类型': error.get('account_type', ''),
                    '公司': error.get('company', ''),
                    '期间': error.get('period', ''),
                    '年份': error.get('year', ''),
                    '错误描述': error.get('message', ''),
                    '差异金额': error.get('difference', ''),
                    '期初净额': error.get('opening_net', ''),
                    '期间净额': error.get('period_net', ''),
                    '期末净额': error.get('closing_net', ''),
                    '预期期末净额': error.get('expected_closing', ''),
                    '凭证借方金额': error.get('voucher_debit', ''),
                    '凭证贷方金额': error.get('voucher_credit', ''),
                    '科目余额借方': error.get('balance_debit', ''),
                    '科目余额贷方': error.get('balance_credit', ''),
                    '借方差异': error.get('debit_difference', ''),
                    '贷方差异': error.get('credit_difference', ''),
                    '上年度': error.get('prev_year', ''),
                    '当年度': error.get('curr_year', ''),
                    '上年期末借方': error.get('prev_closing_debit', ''),
                    '上年期末贷方': error.get('prev_closing_credit', ''),
                    '当年期初借方': error.get('curr_opening_debit', ''),
                    '当年期初贷方': error.get('curr_opening_credit', ''),
                    '父科目': error.get('parent_subject', ''),
                    '验证字段': error.get('field', ''),
                    '父科目值': error.get('parent_value', ''),
                    '子科目汇总': error.get('child_sum', '')
                }
                all_errors.append(error_record)
        
        if all_errors:
            error_df = pd.DataFrame(all_errors)
            # 移除空列
            error_df = error_df.dropna(axis=1, how='all')
            error_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            logger.info(f"CSV错误报告已生成: {csv_path}, 共 {len(all_errors)} 条错误记录")
        else:
            # 如果没有错误，创建一个空的CSV文件
            empty_df = pd.DataFrame([{'结果': '所有验证都通过，没有发现错误'}])
            empty_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            logger.info(f"CSV报告已生成: {csv_path}, 所有验证都通过")

def main():
    """主函数"""
    validator = FinancialDataValidator()
    
    try:
        results = validator.run_all_validations()
        
        if results['total_failed'] == 0:
            logger.info("✅ 所有验证通过!")
        else:
            logger.warning(f"⚠️  发现 {results['total_failed']} 个验证错误")
            
    except Exception as e:
        logger.error(f"验证过程出现错误: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())