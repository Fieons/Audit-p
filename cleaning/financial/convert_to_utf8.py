#!/usr/bin/env python3
"""
编码转换脚本 - 将format-data目录下的所有CSV文件转换为UTF-8格式
"""

import os
import pandas as pd
from pathlib import Path


def detect_encoding(file_path):
    """检测文件的编码格式"""
    # 尝试常见的中文编码
    encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'cp1252', 'iso-8859-1', 'ascii']
    
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read(1024)  # 读取一小部分内容测试
            return encoding
        except UnicodeDecodeError:
            continue
    
    return None


def convert_csv_to_utf8(file_path):
    """将CSV文件转换为UTF-8编码并覆盖原文件"""
    try:
        # 检测当前编码
        current_encoding = detect_encoding(file_path)
        print(f"检测到文件 {file_path} 的编码: {current_encoding}")
        
        # 如果已经是UTF-8，跳过
        if current_encoding and current_encoding.lower() in ['utf-8', 'ascii']:
            print(f"文件 {file_path} 已经是UTF-8编码，跳过")
            return True
            
        # 读取文件并转换编码
        try:
            df = pd.read_csv(file_path, encoding=current_encoding)
        except UnicodeDecodeError:
            # 如果检测的编码失败，尝试常见编码
            encodings_to_try = ['gbk', 'gb2312', 'cp1252', 'iso-8859-1']
            df = None
            for encoding in encodings_to_try:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    current_encoding = encoding
                    print(f"使用 {encoding} 编码成功读取文件")
                    break
                except:
                    continue
            
            if df is None:
                print(f"错误: 无法读取文件 {file_path}")
                return False
        
        # 保存为UTF-8编码，覆盖原文件
        df.to_csv(file_path, encoding='utf-8', index=False)
        print(f"成功转换文件 {file_path} 为UTF-8编码")
        return True
        
    except Exception as e:
        print(f"转换文件 {file_path} 时出错: {str(e)}")
        return False


def main():
    """主函数 - 扫描format-data目录下的所有CSV文件并转换编码"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent.parent
    format_data_dir = project_root / 'format-data'
    
    if not format_data_dir.exists():
        print(f"错误: format-data目录不存在: {format_data_dir}")
        return
    
    # 查找所有CSV文件
    csv_files = list(format_data_dir.rglob('*.csv'))
    
    if not csv_files:
        print("未找到CSV文件")
        return
    
    print(f"找到 {len(csv_files)} 个CSV文件:")
    for file_path in csv_files:
        print(f"  - {file_path}")
    
    print("\n开始转换编码...")
    
    success_count = 0
    fail_count = 0
    
    for file_path in csv_files:
        if convert_csv_to_utf8(file_path):
            success_count += 1
        else:
            fail_count += 1
    
    print(f"\n转换完成:")
    print(f"成功: {success_count} 个文件")
    print(f"失败: {fail_count} 个文件")


if __name__ == "__main__":
    main()