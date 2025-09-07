#!/usr/bin/env python3
"""
期初余额调整脚本
根据期末余额倒推期初余额，确保会计恒等式平衡
适用于2024年和2025年两家公司的所有科目（包括核算维度）
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Tuple
import shutil
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OpeningBalanceAdjuster:
    def __init__(self, data_dir: str = "/home/Fieons/Audit-p/format-data/financial"):
        """初始化期初余额调整器"""
        self.data_dir = Path(data_dir)
        self.balance_df = None
        self.original_file = self.data_dir / "final_enhanced_balance.csv"
        self.backup_file = self.data_dir / f"final_enhanced_balance_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
    def load_data(self):
        """加载科目余额表数据"""
        try:
            logger.info(f"正在加载科目余额表: {self.original_file}")
            
            # 创建备份
            shutil.copy2(self.original_file, self.backup_file)
            logger.info(f"原文件已备份至: {self.backup_file}")
            
            self.balance_df = pd.read_csv(self.original_file, encoding='utf-8')
            logger.info(f"科目余额表形状: {self.balance_df.shape}")
            
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
        
        # 提取年份信息
        self.balance_df['年份'] = self.balance_df['期间'].astype(str).str.extract(r'(\d{4})')[0].astype(float).astype(int)
        
        logger.info(f"数据包含年份: {sorted(self.balance_df['年份'].unique())}")
        logger.info(f"数据包含公司: {self.balance_df['公司'].unique()}")
    
    def _get_account_type(self, row: pd.Series) -> str:
        """
        根据科目编码或subject_code_path判断科目类型
        中国会计准则科目编码规则:
        1xxx: 资产类
        2xxx: 负债类  
        3xxx: 所有者权益类
        4xxx: 收入类
        5xxx: 费用类
        6xxx: 损益类
        """
        # 首先尝试从科目编码获取
        subject_code = str(row['科目编码'])
        if subject_code != 'nan' and subject_code != '':
            code = subject_code.split('.')[0]  # 取主科目编码
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
        
        # 如果科目编码为空，从subject_code_path获取
        subject_code_path = str(row['subject_code_path'])
        if subject_code_path != 'nan' and subject_code_path != '':
            # 从路径中提取科目编码（如 "/1001/" -> "1001"）
            path_parts = [part for part in subject_code_path.split('/') if part]
            if path_parts:
                main_code = path_parts[0]  # 第一个非空部分就是主科目编码
                if main_code.startswith('1'):
                    return 'asset'
                elif main_code.startswith('2'):
                    return 'liability'
                elif main_code.startswith('3'):
                    return 'equity'
                elif main_code.startswith('4'):
                    return 'income'
                elif main_code.startswith('5') or main_code.startswith('6'):
                    return 'expense'
        
        return 'unknown'
    
    def _calculate_opening_balance(self, row: pd.Series) -> Tuple[float, float]:
        """
        根据会计恒等式倒推期初余额
        
        基本公式：期初余额 + 本年累计发生额 = 期末余额
        即：期初余额 = 期末余额 - 本年累计发生额
        
        根据科目类型使用不同的计算逻辑：
        - 资产类: 期初借方 - 期初贷方 = (期末借方 - 期末贷方) - (本年累计借方 - 本年累计贷方)
        - 负债类: 期初贷方 - 期初借方 = (期末贷方 - 期末借方) - (本年累计贷方 - 本年累计借方)
        - 所有者权益类: 期初贷方 - 期初借方 = (期末贷方 - 期末借方) - (本年累计贷方 - 本年累计借方)
        - 收入类: 期初一般为0，按贷方性质计算
        - 费用类: 期初一般为0，按借方性质计算
        """
        account_type = self._get_account_type(row)
        
        # 根据科目类型获取正确的净额计算
        if account_type == 'asset':
            # 资产类: 借方 - 贷方
            closing_net = row['期末余额借方'] - row['期末余额贷方']
            period_net = row['本年累计借方'] - row['本年累计贷方']
            opening_net = closing_net - period_net
            
        elif account_type in ['liability', 'equity']:
            # 负债类和权益类: 贷方 - 借方
            closing_net = row['期末余额贷方'] - row['期末余额借方']
            period_net = row['本年累计贷方'] - row['本年累计借方']
            opening_net = closing_net - period_net
            
        elif account_type == 'income':
            # 收入类: 贷方 - 借方
            closing_net = row['期末余额贷方'] - row['期末余额借方']
            period_net = row['本年累计贷方'] - row['本年累计借方']
            opening_net = closing_net - period_net
            
        elif account_type == 'expense':
            # 费用类: 借方 - 贷方
            closing_net = row['期末余额借方'] - row['期末余额贷方']
            period_net = row['本年累计借方'] - row['本年累计贷方']
            opening_net = closing_net - period_net
            
        else:
            # 未知类型，保持原计算方式
            closing_net = row['期末余额借方'] - row['期末余额贷方']
            period_net = row['本年累计借方'] - row['本年累计贷方']
            opening_net = closing_net - period_net
        
        # 根据科目类型和期初净额的正负，分配到借方或贷方
        if account_type == 'asset':
            # 资产类：正数记借方，负数记贷方
            if opening_net >= 0:
                opening_debit = opening_net
                opening_credit = 0
            else:
                opening_debit = 0
                opening_credit = -opening_net
                
        elif account_type in ['liability', 'equity']:
            # 负债类和权益类：正数记贷方，负数记借方
            if opening_net >= 0:
                opening_debit = 0
                opening_credit = opening_net
            else:
                opening_debit = -opening_net
                opening_credit = 0
                
        elif account_type == 'income':
            # 收入类：一般为贷方余额
            if opening_net >= 0:
                opening_debit = 0
                opening_credit = opening_net
            else:
                opening_debit = -opening_net
                opening_credit = 0
                
        elif account_type == 'expense':
            # 费用类：一般为借方余额
            if opening_net >= 0:
                opening_debit = opening_net
                opening_credit = 0
            else:
                opening_debit = 0
                opening_credit = -opening_net
                
        else:
            # 未知类型，保持原值
            logger.warning(f"未知科目类型: {row['科目编码']} - {account_type}")
            return row['期初余额借方'], row['期初余额贷方']
        
        return opening_debit, opening_credit
    
    def adjust_opening_balances(self):
        """调整2024年和2025年的期初余额"""
        if self.balance_df is None:
            self.load_data()
        
        logger.info("开始调整期初余额...")
        
        # 筛选需要调整的数据（2024年和2025年）
        target_years = [2024, 2025]
        mask = self.balance_df['年份'].isin(target_years)
        target_rows = self.balance_df[mask].copy()
        
        logger.info(f"需要调整的记录数: {len(target_rows)}")
        
        adjustments_made = 0
        
        for idx, row in target_rows.iterrows():
            # 跳过合计行
            if row['科目名称'] == '合计':
                continue
            
            # 计算新的期初余额
            new_opening_debit, new_opening_credit = self._calculate_opening_balance(row)
            
            # 检查是否需要调整
            current_opening_debit = row['期初余额借方']
            current_opening_credit = row['期初余额贷方']
            
            tolerance = 0.01
            needs_adjustment = (
                abs(new_opening_debit - current_opening_debit) > tolerance or
                abs(new_opening_credit - current_opening_credit) > tolerance
            )
            
            if needs_adjustment:
                # 更新期初余额
                self.balance_df.loc[idx, '期初余额借方'] = new_opening_debit
                self.balance_df.loc[idx, '期初余额贷方'] = new_opening_credit
                
                adjustments_made += 1
                
                # 记录调整信息
                account_type = self._get_account_type(row)
                dimension_info = f" 核算维度: {row['核算维度名称']}" if row['is_dimension_row'] else ""
                
                logger.info(
                    f"调整科目 {row['科目编码']} ({row['科目名称']}){dimension_info} [{account_type}类] "
                    f"{row['公司']} {row['年份']}年: "
                    f"期初借方 {current_opening_debit:.2f} -> {new_opening_debit:.2f}, "
                    f"期初贷方 {current_opening_credit:.2f} -> {new_opening_credit:.2f}"
                )
        
        logger.info(f"共调整了 {adjustments_made} 条记录")
        return adjustments_made
    
    def verify_adjustments(self) -> Dict:
        """验证调整后的数据是否符合会计恒等式"""
        logger.info("开始验证调整后的会计恒等式...")
        
        results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
        # 只验证2024年和2025年的数据
        target_years = [2024, 2025]
        mask = self.balance_df['年份'].isin(target_years)
        target_data = self.balance_df[mask]
        
        for idx, row in target_data.iterrows():
            account_type = self._get_account_type(row)
            tolerance = 0.01
            
            # 使用与调整时相同的净额计算逻辑
            # 根据科目类型使用不同的净额计算方式
            if account_type == 'asset':
                opening_net = row['期初余额借方'] - row['期初余额贷方']
                period_net = row['本年累计借方'] - row['本年累计贷方']
                closing_net = row['期末余额借方'] - row['期末余额贷方']
            elif account_type in ['liability', 'equity']:
                opening_net = row['期初余额贷方'] - row['期初余额借方']
                period_net = row['本年累计贷方'] - row['本年累计借方']
                closing_net = row['期末余额贷方'] - row['期末余额借方']
            elif account_type == 'income':
                opening_net = row['期初余额贷方'] - row['期初余额借方']
                period_net = row['本年累计贷方'] - row['本年累计借方']
                closing_net = row['期末余额贷方'] - row['期末余额借方']
            elif account_type == 'expense':
                opening_net = row['期初余额借方'] - row['期初余额贷方']
                period_net = row['本年累计借方'] - row['本年累计贷方']
                closing_net = row['期末余额借方'] - row['期末余额贷方']
            
            expected_closing = opening_net + period_net
            
            # 对于未知类型，仍然进行验证（不应该有未知类型）
            
            # 验证恒等式
            if abs(closing_net - expected_closing) > tolerance:
                dimension_info = f" 核算维度: {row['核算维度名称']}" if row['is_dimension_row'] else ""
                error_msg = (
                    f"科目 {row['科目编码']} ({row['科目名称']}){dimension_info} [{account_type}类] 会计恒等式不平衡: "
                    f"期初净额({opening_net:.2f}) + 发生净额({period_net:.2f}) = {expected_closing:.2f}, "
                    f"但期末净额为 {closing_net:.2f}, 差异: {closing_net - expected_closing:.2f}"
                )
                results['errors'].append(error_msg)
                results['failed'] += 1
            else:
                results['passed'] += 1
        
        logger.info(f"验证完成: 通过 {results['passed']}, 失败 {results['failed']}")
        
        if results['errors']:
            logger.warning("发现以下会计恒等式不平衡的问题:")
            for error in results['errors'][:10]:  # 只显示前10个错误
                logger.warning(f"  - {error}")
            if len(results['errors']) > 10:
                logger.warning(f"  - ... 还有 {len(results['errors']) - 10} 个错误")
        
        return results
    
    def save_adjusted_data(self):
        """保存调整后的数据"""
        try:
            # 保存调整后的数据
            self.balance_df.to_csv(self.original_file, index=False, encoding='utf-8')
            logger.info(f"调整后的数据已保存至: {self.original_file}")
            
            # 生成调整报告
            self._generate_adjustment_report()
            
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
            raise
    
    def _generate_adjustment_report(self):
        """生成调整报告"""
        report_path = self.data_dir / f"opening_balance_adjustment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("期初余额调整报告\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"调整时间: {datetime.now()}\n")
            f.write(f"原始文件: {self.original_file}\n")
            f.write(f"备份文件: {self.backup_file}\n\n")
            
            f.write("调整说明:\n")
            f.write("- 根据会计恒等式倒推期初余额\n")
            f.write("- 公式: 期初余额 = 期末余额 - 本年累计发生额\n")
            f.write("- 适用年份: 2024年, 2025年\n")
            f.write("- 适用范围: 所有科目（包括核算维度）\n\n")
            
            f.write("科目类型处理规则:\n")
            f.write("- 资产类: 正数记借方，负数记贷方\n")
            f.write("- 负债类: 正数记贷方，负数记借方\n")
            f.write("- 所有者权益类: 正数记贷方，负数记借方\n")
            f.write("- 收入类: 正数记贷方，负数记借方\n")
            f.write("- 费用类: 正数记借方，负数记贷方\n\n")
        
        logger.info(f"调整报告已生成: {report_path}")
    
    def run_adjustment(self):
        """执行完整的期初余额调整流程"""
        logger.info("开始执行期初余额调整流程...")
        
        try:
            # 1. 加载数据
            self.load_data()
            
            # 2. 调整期初余额
            adjustments_made = self.adjust_opening_balances()
            
            if adjustments_made == 0:
                logger.info("✅ 所有期初余额都已平衡，无需调整")
                return True
            
            # 3. 验证调整结果
            verification_results = self.verify_adjustments()
            
            if verification_results['failed'] > 0:
                logger.error(f"❌ 调整后仍有 {verification_results['failed']} 条记录不平衡")
                return False
            
            # 4. 保存调整后的数据
            self.save_adjusted_data()
            
            logger.info(f"✅ 期初余额调整完成！共调整 {adjustments_made} 条记录")
            return True
            
        except Exception as e:
            logger.error(f"调整过程出现错误: {e}")
            return False

def main():
    """主函数"""
    adjuster = OpeningBalanceAdjuster()
    
    try:
        success = adjuster.run_adjustment()
        
        if success:
            logger.info("🎉 期初余额调整成功完成!")
            return 0
        else:
            logger.error("💥 期初余额调整失败!")
            return 1
            
    except Exception as e:
        logger.error(f"程序执行出现错误: {e}")
        return 1

if __name__ == "__main__":
    exit(main())