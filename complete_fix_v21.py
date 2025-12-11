#!/usr/bin/env python3
"""
v2.1.0 完整修复脚本
"""

import os
import re
import glob

def fix_environment():
    """设置环境变量"""
    env_fixes = {
        'DISABLE_MODEL_SOURCE_CHECK': 'True',
        'HF_HUB_OFFLINE': '1',
        'OCR_SINGLE_PROCESS': '1',
        'TOKENIZERS_PARALLELISM': 'false',
        'CUDA_VISIBLE_DEVICES': '',  # 强制使用CPU避免GPU问题
    }
    
    for key, value in env_fixes.items():
        os.environ[key] = value
        print(f"✅ 设置 {key}={value}")

def fix_all_paddleocr_files():
    """修复所有包含PaddleOCR的文件"""
    
    # 搜索所有Python文件
    python_files = glob.glob('**/*.py', recursive=True)
    
    fixed_files = []
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否包含PaddleOCR相关代码
            if 'PaddleOCR' in content or 'show_log' in content:
                original_content = content
                
                # 修复各种show_log参数形式
                patterns = [
                    r',\s*',
                    r'\s*',
                    r'',
                    r',\s*',
                    r'\s*',
                    r'',
                ]
                
                for pattern in patterns:
                    content = re.sub(pattern, '', content)
                
                # 如果内容有变化，写回文件
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    fixed_files.append(file_path)
                    
        except Exception as e:
            continue
    
    for file_path in fixed_files:
        print(f"✅ 修复 {file_path}")
    
    return len(fixed_files)

def create_startup_script():
    """创建修复后的启动脚本"""
    script_content = '''#!/bin/bash
export DISABLE_MODEL_SOURCE_CHECK=True
export HF_HUB_OFFLINE=1
export OCR_SINGLE_PROCESS=1
export TOKENIZERS_PARALLELISM=false

echo "🚀 启动 RAG Pro Max v2.1.0 (修复版)"
streamlit run src/apppro.py --server.headless=true
'''
    
    with open('start_v21_fixed.sh', 'w') as f:
        f.write(script_content)
    
    os.chmod('start_v21_fixed.sh', 0o755)
    print("✅ 创建修复启动脚本: start_v21_fixed.sh")

if __name__ == "__main__":
    print("🔧 v2.1.0 完整修复开始...")
    
    fix_environment()
    fixed_count = fix_all_paddleocr_files()
    create_startup_script()
    
    print(f"\n✅ 修复完成！")
    print(f"   修复文件数: {fixed_count}")
    print(f"   环境变量: 已设置")
    print(f"   启动脚本: start_v21_fixed.sh")
    print(f"\n🚀 使用修复启动脚本:")
    print(f"   ./start_v21_fixed.sh")
