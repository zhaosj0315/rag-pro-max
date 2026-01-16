#!/usr/bin/env python3
"""
文档同步检查工具 (Documentation Sync Checker)
版本: v1.0
生成时间: 2026-01-16

功能:
1. 检查版本号一致性
2. 检查 CHANGELOG 是否更新
3. 检查 README 徽章是否正确
4. 生成检查报告
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

# 颜色定义
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def check_version_consistency() -> Tuple[bool, List[str]]:
    """检查版本号一致性"""
    issues = []
    
    # 读取 version.json
    try:
        with open('version.json', 'r', encoding='utf-8') as f:
            version_data = json.load(f)
            version = version_data.get('version', '')
    except Exception as e:
        issues.append(f"❌ 无法读取 version.json: {e}")
        return False, issues
    
    print(f"📌 当前版本: {Colors.BLUE}{version}{Colors.END}")
    print()
    
    # 检查 README.md
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()
            
        # 检查版本徽章
        badge_pattern = r'!\[Version\]\(https://img\.shields\.io/badge/version-v([\d.]+)-'
        badge_match = re.search(badge_pattern, readme_content)
        
        if badge_match:
            readme_version = badge_match.group(1)
            if readme_version == version:
                print(f"  {Colors.GREEN}✓{Colors.END} README.md 版本徽章正确: v{readme_version}")
            else:
                issues.append(f"❌ README.md 版本徽章不一致: v{readme_version} (应为 v{version})")
        else:
            issues.append("❌ README.md 未找到版本徽章")
            
        # 检查版本号文本
        if f"**版本**: v{version}" in readme_content:
            print(f"  {Colors.GREEN}✓{Colors.END} README.md 版本文本正确")
        else:
            issues.append(f"⚠️  README.md 版本文本可能需要更新")
            
    except Exception as e:
        issues.append(f"❌ 无法读取 README.md: {e}")
    
    # 检查 CHANGELOG.md
    try:
        with open('CHANGELOG.md', 'r', encoding='utf-8') as f:
            changelog_content = f.read()
            
        # 检查是否有当前版本的条目
        version_pattern = rf'\[v{re.escape(version)}\]'
        if re.search(version_pattern, changelog_content):
            print(f"  {Colors.GREEN}✓{Colors.END} CHANGELOG.md 包含 v{version} 条目")
        else:
            issues.append(f"❌ CHANGELOG.md 缺少 v{version} 条目")
            
    except Exception as e:
        issues.append(f"❌ 无法读取 CHANGELOG.md: {e}")
    
    print()
    return len(issues) == 0, issues

def check_documentation_completeness() -> Tuple[bool, List[str]]:
    """检查文档完整性"""
    issues = []
    
    required_docs = {
        'README.md': '项目门面',
        'CHANGELOG.md': '版本记录',
        'USER_MANUAL.md': '用户手册',
        'API_DOCUMENTATION.md': 'API文档',
        'ARCHITECTURE.md': '架构说明',
        'DEPLOYMENT.md': '部署指南',
        'TESTING.md': '测试说明',
        'FAQ.md': '常见问题',
        'CONTRIBUTING.md': '贡献指南',
    }
    
    print("📚 检查必需文档...")
    print()
    
    for doc, desc in required_docs.items():
        if Path(doc).exists():
            print(f"  {Colors.GREEN}✓{Colors.END} {doc} ({desc})")
        else:
            issues.append(f"❌ 缺少 {doc} ({desc})")
    
    print()
    return len(issues) == 0, issues

def check_mock_data_docs() -> Tuple[bool, List[str]]:
    """检查 Mock Data 文档"""
    issues = []
    
    print("🔍 检查 Mock Data 文档...")
    print()
    
    mock_docs = [
        'docs/MOCK_DATA_GENERATION.md',
        'docs/MOCK_DATA_QUICKSTART.md',
        'docs/IMPLEMENTATION_SUMMARY_MOCK_DATA.md',
        'docs/TROUBLESHOOTING_MOCK_DATA.md',
    ]
    
    existing_docs = [doc for doc in mock_docs if Path(doc).exists()]
    
    if len(existing_docs) > 2:
        print(f"  {Colors.YELLOW}⚠️{Colors.END}  发现 {len(existing_docs)} 个 Mock Data 文档")
        print(f"  建议: 合并为 2 个文档以减少冗余")
        for doc in existing_docs:
            print(f"    - {doc}")
        issues.append("⚠️  Mock Data 文档过多，建议合并")
    else:
        print(f"  {Colors.GREEN}✓{Colors.END} Mock Data 文档数量合理")
    
    print()
    return len(issues) == 0, issues

def check_test_files() -> Tuple[bool, List[str]]:
    """检查测试文件位置"""
    issues = []
    
    print("🧪 检查测试文件...")
    print()
    
    # 检查根目录是否有测试文件
    root_test_files = list(Path('.').glob('test_*.py'))
    
    if root_test_files:
        print(f"  {Colors.RED}✗{Colors.END} 根目录发现 {len(root_test_files)} 个测试文件:")
        for f in root_test_files:
            print(f"    - {f.name}")
        issues.append(f"❌ 根目录有 {len(root_test_files)} 个测试文件，应移动到 tests/")
    else:
        print(f"  {Colors.GREEN}✓{Colors.END} 根目录无测试文件")
    
    # 检查诊断脚本
    diag_files = ['diagnose_kb.py', 'fix_existing_kb.py']
    existing_diag = [f for f in diag_files if Path(f).exists()]
    
    if existing_diag:
        print(f"  {Colors.RED}✗{Colors.END} 根目录发现 {len(existing_diag)} 个诊断脚本:")
        for f in existing_diag:
            print(f"    - {f}")
        issues.append(f"❌ 根目录有诊断脚本，应移动到 scripts/maintenance/")
    else:
        print(f"  {Colors.GREEN}✓{Colors.END} 根目录无诊断脚本")
    
    print()
    return len(issues) == 0, issues

def check_temp_files() -> Tuple[bool, List[str]]:
    """检查临时文件"""
    issues = []
    
    print("🗑️  检查临时文件...")
    print()
    
    temp_dir = Path('temp_uploads')
    if temp_dir.exists():
        temp_files = list(temp_dir.rglob('*'))
        temp_file_count = len([f for f in temp_files if f.is_file()])
        
        if temp_file_count > 0:
            print(f"  {Colors.RED}✗{Colors.END} temp_uploads/ 包含 {temp_file_count} 个文件")
            issues.append(f"❌ temp_uploads/ 应该被清空")
        else:
            print(f"  {Colors.GREEN}✓{Colors.END} temp_uploads/ 已清空")
    else:
        print(f"  {Colors.GREEN}✓{Colors.END} temp_uploads/ 不存在")
    
    print()
    return len(issues) == 0, issues

def main():
    """主函数"""
    print()
    print("=" * 60)
    print("📋 RAG Pro Max - 文档同步检查工具")
    print("=" * 60)
    print()
    
    all_issues = []
    
    # 执行各项检查
    checks = [
        ("版本一致性", check_version_consistency),
        ("文档完整性", check_documentation_completeness),
        ("Mock Data 文档", check_mock_data_docs),
        ("测试文件位置", check_test_files),
        ("临时文件", check_temp_files),
    ]
    
    results = {}
    for name, check_func in checks:
        success, issues = check_func()
        results[name] = success
        all_issues.extend(issues)
    
    # 生成报告
    print("=" * 60)
    print("📊 检查结果汇总")
    print("=" * 60)
    print()
    
    for name, success in results.items():
        status = f"{Colors.GREEN}✓ 通过{Colors.END}" if success else f"{Colors.RED}✗ 失败{Colors.END}"
        print(f"  {name}: {status}")
    
    print()
    
    if all_issues:
        print(f"{Colors.YELLOW}⚠️  发现 {len(all_issues)} 个问题:{Colors.END}")
        print()
        for issue in all_issues:
            print(f"  {issue}")
        print()
        print(f"{Colors.BLUE}💡 提示:{Colors.END} 运行 scripts/cleanup_materials.sh 自动修复部分问题")
        print()
        return 1
    else:
        print(f"{Colors.GREEN}✅ 所有检查通过！{Colors.END}")
        print()
        return 0

if __name__ == '__main__':
    exit(main())
