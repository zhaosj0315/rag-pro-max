#!/usr/bin/env python3
"""
RAG Pro Max 最终验证与总结报告
生成完整的文档一致性验证报告
"""

import json
import re
import os
from pathlib import Path

def count_modules(directory: str) -> int:
    """统计目录中的Python模块数量"""
    if not os.path.exists(directory):
        return 0
    return len([f for f in os.listdir(directory) if f.endswith('.py') and f != '__init__.py'])

def get_line_count(filepath: str) -> int:
    """获取文件行数"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except:
        return 0

def extract_version_from_json():
    """从version.json提取标准版本号"""
    try:
        with open('version.json', 'r', encoding='utf-8') as f:
            version_data = json.load(f)
            return version_data.get('version', 'unknown')
    except:
        return 'unknown'

def check_readme_consistency():
    """检查README.md的一致性"""
    issues = []
    
    # 获取实际数据
    actual_processors = count_modules('src/processors')
    actual_ui = count_modules('src/ui')
    actual_utils = count_modules('src/utils')
    actual_apppro_lines = get_line_count('src/apppro.py')
    
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查模块数量
        processors_match = re.search(r'processors.*?\((\d+)个模块\)', content)
        ui_match = re.search(r'ui.*?\((\d+)个模块\)', content)
        utils_match = re.search(r'utils.*?\((\d+)个模块\)', content)
        apppro_match = re.search(r'apppro\.py.*?\(([,\d]+) 行\)', content)
        
        if processors_match and int(processors_match.group(1)) != actual_processors:
            issues.append(f"processors模块数不一致: README显示{processors_match.group(1)}, 实际{actual_processors}")
        
        if ui_match and int(ui_match.group(1)) != actual_ui:
            issues.append(f"ui模块数不一致: README显示{ui_match.group(1)}, 实际{actual_ui}")
            
        if utils_match and int(utils_match.group(1)) != actual_utils:
            issues.append(f"utils模块数不一致: README显示{utils_match.group(1)}, 实际{actual_utils}")
            
        if apppro_match:
            readme_lines = int(apppro_match.group(1).replace(',', ''))
            if readme_lines != actual_apppro_lines:
                issues.append(f"apppro.py行数不一致: README显示{readme_lines}, 实际{actual_apppro_lines}")
    
    except Exception as e:
        issues.append(f"无法读取README.md: {e}")
    
    return issues

def check_version_consistency():
    """检查版本号一致性"""
    issues = []
    canonical_version = extract_version_from_json()
    
    # 检查主要文档文件
    files_to_check = [
        'README.md',
        'API_DOCUMENTATION.md', 
        'TESTING.md',
        'FAQ.md',
        'CONTRIBUTING.md'
    ]
    
    for file in files_to_check:
        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找版本号
                version_patterns = [
                    r'version-v(\d+\.\d+\.\d+)',
                    r'版本.*?v(\d+\.\d+\.\d+)',
                    r'Version.*?v(\d+\.\d+\.\d+)'
                ]
                
                found_versions = []
                for pattern in version_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    found_versions.extend(matches)
                
                for version in set(found_versions):
                    if version != canonical_version:
                        issues.append(f"{file}中版本号不一致: 发现{version}, 标准{canonical_version}")
                        
            except Exception as e:
                issues.append(f"无法检查{file}: {e}")
    
    return issues

def generate_final_report():
    """生成最终验证报告"""
    print("=" * 100)
    print("📋 RAG Pro Max 文档一致性最终验证报告")
    print("=" * 100)
    
    # 获取当前系统状态
    canonical_version = extract_version_from_json()
    actual_processors = count_modules('src/processors')
    actual_ui = count_modules('src/ui')
    actual_utils = count_modules('src/utils')
    actual_services = count_modules('src/services')
    actual_common = count_modules('src/common')
    actual_core = count_modules('src/core')
    actual_apppro_lines = get_line_count('src/apppro.py')
    total_modules = actual_processors + actual_ui + actual_utils + actual_services + actual_common + actual_core
    
    print(f"\n📊 当前系统状态 (实际数据):")
    print(f"   版本号: {canonical_version}")
    print(f"   apppro.py 行数: {actual_apppro_lines:,}")
    print(f"   模块统计:")
    print(f"     - processors: {actual_processors} 个")
    print(f"     - ui: {actual_ui} 个")
    print(f"     - utils: {actual_utils} 个")
    print(f"     - services: {actual_services} 个")
    print(f"     - common: {actual_common} 个")
    print(f"     - core: {actual_core} 个")
    print(f"     - 总计: {total_modules} 个模块")
    
    # 检查一致性
    readme_issues = check_readme_consistency()
    version_issues = check_version_consistency()
    
    print(f"\n🔍 一致性检查结果:")
    
    if not readme_issues and not version_issues:
        print("✅ 所有文档信息完全一致！")
        status = "PASS"
    else:
        print(f"❌ 发现 {len(readme_issues + version_issues)} 个不一致问题:")
        
        if readme_issues:
            print(f"\n📄 README.md 问题:")
            for issue in readme_issues:
                print(f"   - {issue}")
        
        if version_issues:
            print(f"\n🔢 版本号问题:")
            for issue in version_issues:
                print(f"   - {issue}")
        
        status = "FAIL"
    
    # 特殊说明
    print(f"\n📝 重要说明:")
    print(f"   ✅ CHANGELOG.md 中的历史版本号 (1.0.0, 1.8.0, 2.2.2, 2.3.1) 是正常的")
    print(f"   ✅ 这些是项目发展历程的记录，不是错误")
    print(f"   ✅ 只有当前版本 {canonical_version} 需要在所有文档中保持一致")
    
    # 生成修复建议
    if readme_issues or version_issues:
        print(f"\n🔧 修复建议:")
        if readme_issues:
            print(f"   1. 更新 README.md 中的模块数量和文件行数")
        if version_issues:
            print(f"   2. 统一所有文档中的当前版本号为 {canonical_version}")
    
    print(f"\n" + "=" * 100)
    if status == "PASS":
        print("🎉 文档一致性验证通过！系统已准备就绪。")
    else:
        print("⚠️  发现文档不一致问题，建议修复后再发布。")
    print("=" * 100)
    
    return status == "PASS"

if __name__ == "__main__":
    success = generate_final_report()
    exit(0 if success else 1)