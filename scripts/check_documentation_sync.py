#!/usr/bin/env python3
"""
RAG Pro Max - 文档同步检查脚本
检查文档是否与代码保持同步
"""

import os
import json
import re
from pathlib import Path

def check_version_consistency():
    """检查版本号一致性"""
    print("🔍 检查版本号一致性...")
    
    # 读取 version.json
    try:
        with open('version.json', 'r') as f:
            version_data = json.load(f)
            current_version = version_data.get('version', 'unknown')
    except:
        print("❌ 无法读取 version.json")
        return False
    
    # 检查 README.md
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()
            if current_version not in readme_content:
                print(f"❌ README.md 中版本号不匹配: {current_version}")
                return False
    except:
        print("❌ 无法读取 README.md")
        return False
    
    print(f"✅ 版本号一致: {current_version}")
    return True

def check_api_documentation():
    """检查API文档完整性"""
    print("\n🔍 检查API文档完整性...")
    
    # 查找API端点
    api_endpoints = []
    src_path = Path('src')
    
    for py_file in src_path.rglob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 查找API装饰器
                endpoints = re.findall(r'@app\.(get|post|put|delete)\(["\']([^"\']+)["\']', content)
                api_endpoints.extend(endpoints)
        except:
            continue
    
    if not api_endpoints:
        print("✅ 没有发现API端点")
        return True
    
    # 检查API.md是否存在
    if not os.path.exists('API.md'):
        print("❌ 发现API端点但缺少 API.md 文档")
        return False
    
    print(f"✅ 发现 {len(api_endpoints)} 个API端点，API.md 存在")
    return True

def check_config_documentation():
    """检查配置文档完整性"""
    print("\n🔍 检查配置文档完整性...")
    
    config_files = list(Path('config').glob('*.json')) if os.path.exists('config') else []
    
    if not config_files:
        print("✅ 没有配置文件需要文档化")
        return True
    
    # 检查 DEPLOYMENT.md 是否提到配置
    try:
        with open('DEPLOYMENT.md', 'r', encoding='utf-8') as f:
            deployment_content = f.read()
            if 'config' not in deployment_content.lower():
                print("❌ DEPLOYMENT.md 中缺少配置说明")
                return False
    except:
        print("❌ 无法读取 DEPLOYMENT.md")
        return False
    
    print(f"✅ 配置文档完整 ({len(config_files)} 个配置文件)")
    return True

def check_feature_documentation():
    """检查功能文档完整性"""
    print("\n🔍 检查功能文档完整性...")
    
    # 检查核心功能是否在文档中
    core_features = [
        'PDF处理', 'OCR识别', '语义检索', '多轮对话', '网页抓取'
    ]
    
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()
            
        missing_features = []
        for feature in core_features:
            if feature not in readme_content:
                missing_features.append(feature)
        
        if missing_features:
            print(f"❌ README.md 中缺少功能说明: {', '.join(missing_features)}")
            return False
            
    except:
        print("❌ 无法读取 README.md")
        return False
    
    print("✅ 核心功能文档完整")
    return True

def main():
    """主检查函数"""
    print("📚 RAG Pro Max 文档同步检查")
    print("=" * 40)
    
    os.chdir(Path(__file__).parent.parent)
    
    checks = [
        check_version_consistency,
        check_api_documentation, 
        check_config_documentation,
        check_feature_documentation
    ]
    
    results = []
    for check in checks:
        results.append(check())
    
    print("\n" + "=" * 40)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ 所有检查通过 ({passed}/{total})")
        print("📚 文档与代码保持同步！")
        return 0
    else:
        print(f"❌ 检查失败 ({passed}/{total})")
        print("📝 请更新相关文档后重试")
        return 1

if __name__ == "__main__":
    exit(main())
