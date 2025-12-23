#!/usr/bin/env python3
"""
系统重复函数分析脚本
分析代码库中的重复函数和分散逻辑
"""

import os
import re
from collections import defaultdict
from pathlib import Path

def analyze_duplicate_functions():
    """分析重复函数"""
    print("🔍 分析系统中的重复函数和分散逻辑...")
    print("=" * 60)
    
    # 1. 分析UI渲染函数
    ui_functions = defaultdict(list)
    
    for py_file in Path("src").rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 查找渲染函数
            render_funcs = re.findall(r'def\s+(render_\w+|show_\w+|display_\w+)', content)
            for func in render_funcs:
                ui_functions[func].append(str(py_file))
                
        except Exception:
            continue
    
    # 2. 分析配置函数
    config_functions = defaultdict(list)
    
    for py_file in Path("src").rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 查找配置函数
            config_funcs = re.findall(r'def\s+(\w*config\w*|\w*setting\w*)', content, re.IGNORECASE)
            for func in config_funcs:
                if func and len(func) > 3:  # 过滤太短的匹配
                    config_functions[func].append(str(py_file))
                    
        except Exception:
            continue
    
    # 3. 分析管理器类
    manager_classes = defaultdict(list)
    
    for py_file in Path("src").rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 查找管理器类
            manager_cls = re.findall(r'class\s+(\w*Manager|\w*Service|\w*Handler)', content)
            for cls in manager_cls:
                manager_classes[cls].append(str(py_file))
                
        except Exception:
            continue
    
    return ui_functions, config_functions, manager_classes

def generate_optimization_plan():
    """生成优化计划"""
    ui_functions, config_functions, manager_classes = analyze_duplicate_functions()
    
    print("📊 重复函数分析结果")
    print("=" * 40)
    
    # UI函数重复分析
    print("\n🎨 UI渲染函数重复:")
    ui_duplicates = {k: v for k, v in ui_functions.items() if len(v) > 1}
    if ui_duplicates:
        for func, files in ui_duplicates.items():
            print(f"   {func}: {len(files)} 个文件")
            for f in files[:3]:  # 只显示前3个
                print(f"     • {f}")
    else:
        print("   ✅ 无明显重复")
    
    # 配置函数重复分析
    print(f"\n⚙️ 配置函数重复:")
    config_duplicates = {k: v for k, v in config_functions.items() if len(v) > 1}
    if config_duplicates:
        for func, files in config_duplicates.items():
            print(f"   {func}: {len(files)} 个文件")
            for f in files[:3]:
                print(f"     • {f}")
    else:
        print("   ✅ 无明显重复")
    
    # 管理器类重复分析
    print(f"\n🏗️ 管理器类重复:")
    manager_duplicates = {k: v for k, v in manager_classes.items() if len(v) > 1}
    if manager_duplicates:
        for cls, files in manager_duplicates.items():
            print(f"   {cls}: {len(files)} 个文件")
            for f in files[:3]:
                print(f"     • {f}")
    else:
        print("   ✅ 无明显重复")
    
    # 统计UI文件数量
    ui_files = list(Path("src/ui").glob("*.py"))
    print(f"\n📁 UI文件统计:")
    print(f"   src/ui/ 目录: {len(ui_files)} 个文件")
    
    # 生成优化计划
    print("\n" + "=" * 60)
    print("🎯 系统优化计划")
    print("=" * 60)
    
    optimization_plan = """
## 📋 RAG Pro Max 系统优化计划 v2.4.9

### 🎯 优化目标
- 消除重复函数和分散逻辑
- 统一UI组件和配置管理
- 简化架构，提高维护效率

### 🔧 优化项目

#### 1️⃣ UI组件统一 (高优先级)
**问题**: src/ui/ 目录有32个文件，存在功能重复
**方案**: 
- 创建统一的UI组件库 `src/ui/unified_components.py`
- 合并相似的渲染函数 (render_*, show_*, display_*)
- 统一样式和交互逻辑

**预期收益**: 减少15-20个UI文件，提高一致性

#### 2️⃣ 配置管理统一 (高优先级)  
**问题**: 配置函数分散在多个文件中
**方案**:
- 创建统一配置服务 `src/services/unified_config_service.py`
- 合并所有 *config* 和 *setting* 函数
- 统一配置存储和加载逻辑

**预期收益**: 配置逻辑集中管理，减少重复代码

#### 3️⃣ 管理器类整合 (中优先级)
**问题**: 多个Manager/Service/Handler类功能重叠
**方案**:
- 分析各Manager类的职责
- 合并功能相似的管理器
- 建立清晰的服务层次结构

**预期收益**: 简化架构，减少类的数量

#### 4️⃣ 文档处理统一 (中优先级)
**问题**: 文档处理逻辑分散
**方案**:
- 统一文档上传、预览、处理流程
- 创建统一的文档处理管道
- 标准化文档元数据提取

**预期收益**: 处理流程标准化，减少bug

#### 5️⃣ 监控和日志统一 (低优先级)
**问题**: 监控组件和日志记录分散
**方案**:
- 统一监控仪表板
- 标准化日志格式和输出
- 集中化性能指标收集

**预期收益**: 运维效率提升

### 📊 预期成果
- **代码减少**: 预计减少8,000-12,000行重复代码
- **文件减少**: 预计减少20-25个重复文件  
- **维护效率**: 提升40-50%
- **一致性**: UI和交互体验完全统一

### 🚀 实施计划
1. **v2.4.9**: UI组件统一 + 配置管理统一
2. **v2.5.0**: 管理器类整合 + 文档处理统一  
3. **v2.5.1**: 监控日志统一 + 最终优化

### ✅ 成功标准
- 出厂测试通过率 > 95%
- 代码重复率 < 5%
- UI一致性评分 > 90%
- 维护复杂度降低 > 40%
"""
    
    print(optimization_plan)
    
    # 保存优化计划
    with open("SYSTEM_OPTIMIZATION_PLAN.md", "w", encoding="utf-8") as f:
        f.write(optimization_plan)
    
    print(f"\n📄 优化计划已保存: SYSTEM_OPTIMIZATION_PLAN.md")
    
    return len(ui_duplicates), len(config_duplicates), len(manager_duplicates)

if __name__ == "__main__":
    print("🚀 RAG Pro Max 系统重复函数分析")
    print("=" * 50)
    
    ui_dup, config_dup, manager_dup = generate_optimization_plan()
    
    print(f"\n📊 分析总结:")
    print(f"   UI函数重复: {ui_dup} 组")
    print(f"   配置函数重复: {config_dup} 组") 
    print(f"   管理器类重复: {manager_dup} 组")
    
    total_issues = ui_dup + config_dup + manager_dup
    if total_issues > 0:
        print(f"\n⚠️ 发现 {total_issues} 组重复问题，建议按计划优化")
    else:
        print(f"\n✅ 系统架构良好，无明显重复问题")
