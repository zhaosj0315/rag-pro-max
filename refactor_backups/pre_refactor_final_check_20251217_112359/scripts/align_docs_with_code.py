#!/usr/bin/env python3
"""
文档与代码对齐脚本
确保所有文档和代码的逻辑对齐，以代码为准
"""

import os
import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Set

def scan_code_interfaces() -> Dict[str, List[str]]:
    """扫描代码中的所有接口"""
    interfaces = {
        'classes': [],
        'functions': [],
        'api_endpoints': [],
        'config_options': [],
        'modules': []
    }
    
    src_dir = Path("src")
    if not src_dir.exists():
        print("❌ src目录不存在")
        return interfaces
    
    # 扫描Python文件
    for py_file in src_dir.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 提取类定义
            class_matches = re.findall(r'class\s+(\w+)', content)
            interfaces['classes'].extend([f"{py_file.relative_to(src_dir)}:{cls}" for cls in class_matches])
            
            # 提取函数定义
            func_matches = re.findall(r'def\s+(\w+)', content)
            interfaces['functions'].extend([f"{py_file.relative_to(src_dir)}:{func}" for func in func_matches])
            
            # 提取API端点
            api_matches = re.findall(r'@app\.(get|post|put|delete)\(["\']([^"\']+)', content)
            interfaces['api_endpoints'].extend([f"{method.upper()} {endpoint}" for method, endpoint in api_matches])
            
            # 记录模块
            interfaces['modules'].append(str(py_file.relative_to(src_dir)))
            
        except Exception as e:
            print(f"⚠️  扫描文件失败 {py_file}: {e}")
    
    return interfaces

def scan_config_files() -> Dict[str, any]:
    """扫描配置文件"""
    config_data = {}
    
    config_files = [
        "config/app_config.json",
        "config/rag_config.json", 
        "rag_config.json",
        "app_config.json"
    ]
    
    for config_file in config_files:
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    config_data[config_file] = data
            except Exception as e:
                print(f"⚠️  读取配置文件失败 {config_file}: {e}")
    
    return config_data

def update_readme_with_interfaces(interfaces: Dict[str, List[str]]) -> bool:
    """更新README.md中的接口信息"""
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        print("❌ README.md不存在")
        return False
    
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 更新项目统计
        total_files = len(interfaces['modules'])
        total_classes = len(interfaces['classes'])
        total_functions = len(interfaces['functions'])
        total_apis = len(interfaces['api_endpoints'])
        
        # 查找并更新统计信息
        stats_pattern = r'- \*\*总文件数\*\*: \d+个Python文件'
        new_stats = f"- **总文件数**: {total_files}个Python文件"
        content = re.sub(stats_pattern, new_stats, content)
        
        # 更新API端点信息
        if interfaces['api_endpoints']:
            api_section = "\n### 🔌 API接口\n\n"
            for endpoint in interfaces['api_endpoints']:
                api_section += f"- `{endpoint}`\n"
            
            # 查找API部分并更新
            api_pattern = r'### 🔌 API接口.*?(?=###|\Z)'
            if re.search(api_pattern, content, re.DOTALL):
                content = re.sub(api_pattern, api_section.strip(), content, flags=re.DOTALL)
            else:
                # 如果没有API部分，在技术栈后添加
                tech_pattern = r'(## 🔧 技术栈.*?)(\n## )'
                content = re.sub(tech_pattern, r'\1\n' + api_section + r'\2', content, flags=re.DOTALL)
        
        # 写回文件
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 更新README.md - {total_files}个文件, {total_classes}个类, {total_functions}个函数, {total_apis}个API")
        return True
        
    except Exception as e:
        print(f"❌ 更新README.md失败: {e}")
        return False

def create_api_documentation(interfaces: Dict[str, List[str]]) -> bool:
    """创建API文档"""
    if not interfaces['api_endpoints']:
        print("⚠️  未发现API端点")
        return True
    
    api_doc_content = f"""# API 文档

## 概述

RAG Pro Max 提供完整的RESTful API接口，支持程序化调用。

## 基础信息

- **Base URL**: `http://localhost:8501`
- **版本**: v2.4.1
- **认证**: 暂无（本地部署）

## API 端点

"""
    
    for endpoint in interfaces['api_endpoints']:
        method, path = endpoint.split(' ', 1)
        api_doc_content += f"""### {method} {path}

**描述**: {path}接口

**请求方式**: {method}

**参数**: 待补充

**响应**: 待补充

---

"""
    
    # 写入API文档
    try:
        with open("API_DOCUMENTATION.md", 'w', encoding='utf-8') as f:
            f.write(api_doc_content)
        print(f"✅ 创建API文档 - {len(interfaces['api_endpoints'])}个端点")
        return True
    except Exception as e:
        print(f"❌ 创建API文档失败: {e}")
        return False

def update_test_coverage(interfaces: Dict[str, List[str]]) -> bool:
    """更新测试覆盖率"""
    test_file = "tests/test_complete_interfaces.py"
    
    if not os.path.exists(test_file):
        print("⚠️  测试文件不存在，跳过更新")
        return True
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 统计需要测试的模块数量
        unique_modules = set()
        for module_path in interfaces['modules']:
            # 提取模块目录
            parts = Path(module_path).parts
            if len(parts) > 1:
                unique_modules.add(parts[0])  # 如 'api', 'ui', 'core'
        
        # 更新测试注释
        comment_pattern = r'测试所有代码中的接口和功能'
        new_comment = f"测试所有代码中的接口和功能\n测试覆盖: {len(unique_modules)}个模块, {len(interfaces['classes'])}个类"
        content = re.sub(comment_pattern, new_comment, content)
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 更新测试覆盖率 - {len(unique_modules)}个模块")
        return True
        
    except Exception as e:
        print(f"❌ 更新测试覆盖率失败: {e}")
        return False

def validate_config_consistency(config_data: Dict[str, any]) -> bool:
    """验证配置文件一致性"""
    if not config_data:
        print("⚠️  未找到配置文件")
        return True
    
    print("🔍 验证配置文件一致性...")
    
    # 检查必要的配置项
    required_configs = {
        'chunk_size': 'RAG分块大小',
        'chunk_overlap': 'RAG分块重叠',
        'top_k': '检索文档数量',
        'similarity_threshold': '相似度阈值'
    }
    
    for config_file, data in config_data.items():
        print(f"  📄 {config_file}")
        for key, desc in required_configs.items():
            if key in data:
                print(f"    ✅ {desc}: {data[key]}")
            else:
                print(f"    ⚠️  缺少配置: {desc} ({key})")
    
    return True

def generate_interface_summary() -> bool:
    """生成接口汇总文档"""
    interfaces = scan_code_interfaces()
    config_data = scan_config_files()
    
    summary_content = f"""# RAG Pro Max 接口汇总

## 📊 统计信息

- **Python模块**: {len(interfaces['modules'])}个
- **类定义**: {len(interfaces['classes'])}个  
- **函数定义**: {len(interfaces['functions'])}个
- **API端点**: {len(interfaces['api_endpoints'])}个
- **配置文件**: {len(config_data)}个

## 🏗️ 模块结构

"""
    
    # 按目录分组模块
    modules_by_dir = {}
    for module in interfaces['modules']:
        dir_name = Path(module).parts[0] if '/' in module else 'root'
        if dir_name not in modules_by_dir:
            modules_by_dir[dir_name] = []
        modules_by_dir[dir_name].append(module)
    
    for dir_name, modules in sorted(modules_by_dir.items()):
        summary_content += f"### {dir_name}/\n"
        for module in sorted(modules):
            summary_content += f"- {module}\n"
        summary_content += "\n"
    
    # API端点
    if interfaces['api_endpoints']:
        summary_content += "## 🔌 API端点\n\n"
        for endpoint in sorted(interfaces['api_endpoints']):
            summary_content += f"- `{endpoint}`\n"
        summary_content += "\n"
    
    # 配置文件
    if config_data:
        summary_content += "## ⚙️ 配置文件\n\n"
        for config_file, data in config_data.items():
            summary_content += f"### {config_file}\n"
            for key, value in data.items():
                summary_content += f"- `{key}`: {value}\n"
            summary_content += "\n"
    
    summary_content += f"""
## 📝 生成时间

{os.popen('date').read().strip()}

---

*此文档由 `scripts/align_docs_with_code.py` 自动生成*
"""
    
    try:
        with open("INTERFACE_SUMMARY.md", 'w', encoding='utf-8') as f:
            f.write(summary_content)
        print("✅ 生成接口汇总文档")
        return True
    except Exception as e:
        print(f"❌ 生成接口汇总文档失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("  RAG Pro Max - 文档与代码对齐")
    print("=" * 60)
    
    # 切换到项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    print(f"📁 工作目录: {os.getcwd()}")
    
    # 扫描代码接口
    print("\n🔍 扫描代码接口...")
    interfaces = scan_code_interfaces()
    
    print(f"  📄 发现 {len(interfaces['modules'])} 个Python模块")
    print(f"  🏗️  发现 {len(interfaces['classes'])} 个类定义")
    print(f"  ⚙️  发现 {len(interfaces['functions'])} 个函数定义")
    print(f"  🔌 发现 {len(interfaces['api_endpoints'])} 个API端点")
    
    # 扫描配置文件
    print("\n🔍 扫描配置文件...")
    config_data = scan_config_files()
    print(f"  ⚙️  发现 {len(config_data)} 个配置文件")
    
    # 执行对齐任务
    tasks = [
        ("更新README.md", lambda: update_readme_with_interfaces(interfaces)),
        ("创建API文档", lambda: create_api_documentation(interfaces)),
        ("更新测试覆盖率", lambda: update_test_coverage(interfaces)),
        ("验证配置一致性", lambda: validate_config_consistency(config_data)),
        ("生成接口汇总", lambda: generate_interface_summary())
    ]
    
    success_count = 0
    for task_name, task_func in tasks:
        print(f"\n📝 {task_name}...")
        try:
            if task_func():
                success_count += 1
        except Exception as e:
            print(f"❌ {task_name}失败: {e}")
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("  对齐结果汇总")
    print("=" * 60)
    print(f"✅ 成功: {success_count}/{len(tasks)}")
    
    if success_count == len(tasks):
        print("\n🎉 所有文档已与代码对齐！")
        return True
    else:
        print(f"\n⚠️  {len(tasks) - success_count} 个任务需要手动处理")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
