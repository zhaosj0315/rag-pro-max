#!/usr/bin/env python3
"""
测试覆盖率分析工具
分析项目的测试覆盖情况
"""

import os
import sys
import glob
import importlib.util
from pathlib import Path

def analyze_test_coverage():
    """分析测试覆盖率"""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"
    tests_dir = project_root / "tests"
    
    print("=" * 60)
    print("  RAG Pro Max 测试覆盖率分析")
    print("=" * 60)
    
    # 统计源文件
    py_files = list(src_dir.rglob("*.py"))
    py_files = [f for f in py_files if not f.name.startswith("__")]
    
    # 统计测试文件
    test_files = list(tests_dir.glob("test_*.py"))
    
    print(f"\n📊 文件统计:")
    print(f"源文件数量: {len(py_files)}")
    print(f"测试文件数量: {len(test_files)}")
    
    # 分析模块覆盖
    print(f"\n🔍 模块覆盖分析:")
    
    covered_modules = set()
    uncovered_modules = []
    
    # 检查每个测试文件覆盖的模块
    for test_file in test_files:
        print(f"✅ {test_file.name}")
        
        # 简单的启发式：从测试文件名推断覆盖的模块
        if "stage" in test_file.name:
            stage_num = test_file.name.split("stage")[1].split("_")[0]
            covered_modules.add(f"Stage {stage_num} modules")
        elif "factory" in test_file.name:
            covered_modules.add("Factory test (全系统)")
        else:
            module_name = test_file.name.replace("test_", "").replace(".py", "")
            covered_modules.add(module_name)
    
    # 检查未覆盖的模块
    for py_file in py_files:
        rel_path = py_file.relative_to(src_dir)
        if rel_path.name not in ["__init__.py", "apppro.py"]:
            module_path = str(rel_path).replace("/", ".").replace(".py", "")
            # 简化检查：如果没有对应的测试文件，认为未覆盖
            test_exists = any(module_path.split(".")[-1] in tf.name for tf in test_files)
            if not test_exists and "apppro" not in module_path:
                uncovered_modules.append(module_path)
    
    print(f"\n📈 覆盖率统计:")
    total_modules = len(py_files) - 1  # 排除主文件
    covered_count = len(covered_modules)
    coverage_rate = (covered_count / total_modules) * 100 if total_modules > 0 else 0
    
    print(f"已覆盖模块: {covered_count}")
    print(f"总模块数: {total_modules}")
    print(f"覆盖率: {coverage_rate:.1f}%")
    
    # 显示未覆盖的模块
    if uncovered_modules:
        print(f"\n⚠️ 未覆盖的模块 ({len(uncovered_modules)} 个):")
        for module in uncovered_modules[:10]:  # 只显示前10个
            print(f"  - {module}")
        if len(uncovered_modules) > 10:
            print(f"  ... 还有 {len(uncovered_modules) - 10} 个")
    
    # 测试质量分析
    print(f"\n🎯 测试质量分析:")
    
    total_test_lines = 0
    for test_file in test_files:
        try:
            with open(test_file, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
                total_test_lines += lines
                print(f"  {test_file.name}: {lines} 行")
        except:
            pass
    
    print(f"\n总测试代码: {total_test_lines} 行")
    
    # 建议
    print(f"\n💡 改进建议:")
    if coverage_rate < 80:
        print("  - 测试覆盖率偏低，建议增加单元测试")
    if coverage_rate < 90:
        print("  - 为核心模块添加更多测试用例")
    if len(uncovered_modules) > 5:
        print("  - 优先为未覆盖的核心模块添加测试")
    
    print(f"\n🎯 目标:")
    print(f"  - 目标覆盖率: 100%")
    print(f"  - 需要增加: {100 - coverage_rate:.1f}%")
    
    return coverage_rate >= 90

if __name__ == "__main__":
    success = analyze_test_coverage()
    sys.exit(0 if success else 1)
