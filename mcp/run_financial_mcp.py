#!/usr/bin/env python3
"""
财务数据 MCP 服务器启动包装脚本
自动检测并使用虚拟环境的 Python
"""

import os
import sys
import subprocess
from pathlib import Path

def find_virtualenv_python():
    """查找虚拟环境中的 Python 解释器"""
    project_root = Path(__file__).parent.parent
    
    # 检查 Windows 虚拟环境
    venv_python_win = project_root / "venv" / "Scripts" / "python.exe"
    if venv_python_win.exists():
        return str(venv_python_win)
    
    # 检查 Unix 虚拟环境
    venv_python_unix = project_root / "venv" / "bin" / "python"
    if venv_python_unix.exists():
        return str(venv_python_unix)
    
    # 如果没有找到虚拟环境，使用系统 Python
    return sys.executable

def main():
    python_executable = find_virtualenv_python()
    mcp_script = str(Path(__file__).parent / "financial_data_mcp.py")
    
    print(f"使用 Python: {python_executable}")
    print(f"运行 MCP 服务器: {mcp_script}")
    
    # 运行 MCP 服务器
    result = subprocess.run([python_executable, mcp_script], 
                          cwd=str(Path(__file__).parent.parent))
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())