#!/usr/bin/env python3
"""
模块重复建设审查工具 - 检查项目中的重复模块和功能
"""

import os
import ast
from pathlib import Path
from collections import defaultdict
import difflib

class ModuleDuplicationChecker:
    def __init__(self, src_dir="src"):
        self.src_dir = Path(src_dir)
        self.modules = {}
        self.functions = defaultdict(list)
        self.classes = defaultdict(list)
        self.imports = defaultdict(list)
        
    def scan_all_modules(self):
        """扫描所有Python模块"""
        for py_file in self.src_dir.rglob("*.py"):
            if py_file.name.startswith('__'):
                continue
            self.analyze_module(py_file)
            
    def analyze_module(self, file_path):
        """分析单个模块"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            module_info = {
                'path': file_path,
                'functions': [],
                'classes': [],
                'imports': []
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_name = node.name
                    module_info['functions'].append(func_name)
                    self.functions[func_name].append(str(file_path))
                    
                elif isinstance(node, ast.ClassDef):
                    class_name = node.name
                    module_info['classes'].append(class_name)
                    self.classes[class_name].append(str(file_path))
                    
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            module_info['imports'].append(alias.name)
                    else:
                        module = node.module or ''
                        for alias in node.names:
                            import_name = f"{module}.{alias.name}" if module else alias.name
                            module_info['imports'].append(import_name)
                            
            self.modules[str(file_path)] = module_info
            
        except Exception as e:
            print(f"⚠️ 分析失败: {file_path} - {e}")
            
    def find_duplicate_functions(self):
        """查找重复的函数名"""
        duplicates = {}
        for func_name, locations in self.functions.items():
            if len(locations) > 1:
                duplicates[func_name] = locations
        return duplicates
        
    def find_duplicate_classes(self):
        """查找重复的类名"""
        duplicates = {}
        for class_name, locations in self.classes.items():
            if len(locations) > 1:
                duplicates[class_name] = locations
        return duplicates
        
    def find_similar_modules(self, threshold=0.7):
        """查找相似的模块"""
        similar_pairs = []
        module_paths = list(self.modules.keys())
        
        for i, path1 in enumerate(module_paths):
            for path2 in module_paths[i+1:]:
                similarity = self.calculate_module_similarity(path1, path2)
                if similarity > threshold:
                    similar_pairs.append((path1, path2, similarity))
                    
        return sorted(similar_pairs, key=lambda x: x[2], reverse=True)
        
    def calculate_module_similarity(self, path1, path2):
        """计算两个模块的相似度"""
        module1 = self.modules[path1]
        module2 = self.modules[path2]
        
        # 比较函数名
        funcs1 = set(module1['functions'])
        funcs2 = set(module2['functions'])
        func_similarity = len(funcs1 & funcs2) / max(len(funcs1 | funcs2), 1)
        
        # 比较类名
        classes1 = set(module1['classes'])
        classes2 = set(module2['classes'])
        class_similarity = len(classes1 & classes2) / max(len(classes1 | classes2), 1)
        
        # 比较导入
        imports1 = set(module1['imports'])
        imports2 = set(module2['imports'])
        import_similarity = len(imports1 & imports2) / max(len(imports1 | imports2), 1)
        
        # 加权平均
        return (func_similarity * 0.5 + class_similarity * 0.3 + import_similarity * 0.2)
        
    def find_redundant_modules(self):
        """查找冗余模块"""
        redundant = []
        
        # 检查空模块或几乎空的模块
        for path, info in self.modules.items():
            total_items = len(info['functions']) + len(info['classes'])
            if total_items <= 1:
                redundant.append({
                    'path': path,
                    'reason': '模块几乎为空',
                    'items': total_items
                })
                
        # 检查只有一个函数且函数名与文件名相同的模块
        for path, info in self.modules.items():
            if len(info['functions']) == 1 and len(info['classes']) == 0:
                func_name = info['functions'][0]
                file_name = Path(path).stem
                if func_name.lower() == file_name.lower().replace('_', ''):
                    redundant.append({
                        'path': path,
                        'reason': '单函数模块，可能可以合并',
                        'function': func_name
                    })
                    
        return redundant
        
    def generate_report(self):
        """生成重复建设审查报告"""
        print("🔍 模块重复建设审查报告")
        print("=" * 60)
        
        self.scan_all_modules()
        
        print(f"📊 扫描结果: {len(self.modules)} 个模块")
        print()
        
        # 1. 重复函数
        dup_funcs = self.find_duplicate_functions()
        if dup_funcs:
            print("🔄 重复函数名:")
            for func_name, locations in dup_funcs.items():
                print(f"  📝 {func_name}:")
                for loc in locations:
                    print(f"    - {loc}")
            print()
        else:
            print("✅ 未发现重复函数名")
            print()
            
        # 2. 重复类
        dup_classes = self.find_duplicate_classes()
        if dup_classes:
            print("🔄 重复类名:")
            for class_name, locations in dup_classes.items():
                print(f"  📝 {class_name}:")
                for loc in locations:
                    print(f"    - {loc}")
            print()
        else:
            print("✅ 未发现重复类名")
            print()
            
        # 3. 相似模块
        similar = self.find_similar_modules()
        if similar:
            print("🔍 相似模块 (可能重复建设):")
            for path1, path2, similarity in similar[:10]:  # 只显示前10个
                print(f"  📊 相似度 {similarity:.2%}:")
                print(f"    - {path1}")
                print(f"    - {path2}")
            print()
        else:
            print("✅ 未发现高度相似的模块")
            print()
            
        # 4. 冗余模块
        redundant = self.find_redundant_modules()
        if redundant:
            print("🗑️ 可能冗余的模块:")
            for item in redundant:
                print(f"  📁 {item['path']}")
                print(f"    理由: {item['reason']}")
                if 'items' in item:
                    print(f"    项目数: {item['items']}")
                if 'function' in item:
                    print(f"    函数: {item['function']}")
            print()
        else:
            print("✅ 未发现明显冗余的模块")
            print()
            
        # 5. 统计摘要
        print("📈 统计摘要:")
        print(f"  - 总模块数: {len(self.modules)}")
        print(f"  - 重复函数: {len(dup_funcs)}")
        print(f"  - 重复类: {len(dup_classes)}")
        print(f"  - 相似模块对: {len(similar)}")
        print(f"  - 可能冗余模块: {len(redundant)}")
        
        # 6. 建议
        print("\n💡 重构建议:")
        if dup_funcs:
            print("  1. 合并或重命名重复函数")
        if dup_classes:
            print("  2. 合并或重命名重复类")
        if similar:
            print("  3. 考虑合并高度相似的模块")
        if redundant:
            print("  4. 清理或合并冗余模块")
        if not any([dup_funcs, dup_classes, similar, redundant]):
            print("  ✅ 模块结构良好，无明显重复建设")
            
        return {
            'duplicate_functions': dup_funcs,
            'duplicate_classes': dup_classes,
            'similar_modules': similar,
            'redundant_modules': redundant
        }

def main():
    checker = ModuleDuplicationChecker()
    checker.generate_report()

if __name__ == "__main__":
    main()
