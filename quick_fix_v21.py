#!/usr/bin/env python3
"""
v2.1.0 快速修复脚本
"""

import os
import subprocess

def fix_offline_mode():
    """启用离线模式"""
    os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
    os.environ['HF_HUB_OFFLINE'] = '1'
    print("✅ 离线模式已启用")

def fix_ocr_multiprocessing():
    """修复OCR多进程问题"""
    # 设置单进程模式
    os.environ['OCR_SINGLE_PROCESS'] = '1'
    print("✅ OCR单进程模式已启用")

def apply_fixes():
    """应用所有修复"""
    print("🔧 应用v2.1.0快速修复...")
    
    fix_offline_mode()
    fix_ocr_multiprocessing()
    
    print("\n✅ 修复完成！现在重启应用:")
    print("   streamlit run src/apppro.py")

if __name__ == "__main__":
    apply_fixes()
