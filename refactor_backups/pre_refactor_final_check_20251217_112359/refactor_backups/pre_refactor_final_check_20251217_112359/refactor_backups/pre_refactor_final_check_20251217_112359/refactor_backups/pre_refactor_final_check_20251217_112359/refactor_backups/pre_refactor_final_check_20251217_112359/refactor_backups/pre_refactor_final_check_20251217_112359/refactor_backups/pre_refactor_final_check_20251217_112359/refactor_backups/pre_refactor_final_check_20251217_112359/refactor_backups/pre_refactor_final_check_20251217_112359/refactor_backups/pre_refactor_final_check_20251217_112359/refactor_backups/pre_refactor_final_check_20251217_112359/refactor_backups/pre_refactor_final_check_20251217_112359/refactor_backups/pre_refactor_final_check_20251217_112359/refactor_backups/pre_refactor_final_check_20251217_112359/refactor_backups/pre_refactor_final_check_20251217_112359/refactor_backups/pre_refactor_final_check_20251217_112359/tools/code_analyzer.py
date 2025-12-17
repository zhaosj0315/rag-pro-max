#!/usr/bin/env python3
"""
代码分析工具 - 重构前分析代码质量
"""

import ast
import os
from collections import defaultdict
from pathlib import Path

class CodeAnalyzer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.tree = None
        self.functions = []
        self.classes = []
        self.imports = []
        
    def parse_file(self):
        """解析Python文件"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.tree = ast.parse(content)
        
    def analyze_functions(self):
        """分析函数复杂度"""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    'name': node.name,
                    'line_start': node.lineno,
                    'line_end': node.end_lineno or node.lineno,
                    'lines': (node.end_lineno or node.lineno) - node.lineno + 1,
                    'complexity': self._calculate_complexity(node),
                    'args_count': len(node.args.args)
                }
                self.functions.append(func_info)
                
    def _calculate_complexity(self, node):
        """计算圈复杂度"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
        
    def find_duplicates(self):
        """查找重复代码模式"""
        # 简化版：查找相同的函数名
        func_names = [f['name'] for f in self.functions]
        duplicates = []
        seen = set()
        for name in func_names:
            if name in seen:
                duplicates.append(name)
            seen.add(name)
        return duplicates
        
    def analyze_imports(self):
        """分析导入依赖"""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    self.imports.append(f"{module}.{alias.name}")
                    
    def generate_report(self):
        """生成分析报告"""
        self.parse_file()
        self.analyze_functions()
        self.analyze_imports()
        
        report = {
            'file': self.file_path,
            'total_lines': sum(1 for _ in open(self.file_path)),
            'functions_count': len(self.functions),
            'large_functions': [f for f in self.functions if f['lines'] > 50],
            'complex_functions': [f for f in self.functions if f['complexity'] > 10],
            'duplicates': self.find_duplicates(),
            'imports_count': len(set(self.imports))
        }
        
        return report

def analyze_main_file():
    """分析主文件apppro.py"""
    analyzer = CodeAnalyzer('src/apppro.py')
    report = analyzer.generate_report()
    
    print("🔍 代码分析报告")
    print("=" * 50)
    print(f"文件: {report['file']}")
    print(f"总行数: {report['total_lines']}")
    print(f"函数数量: {report['functions_count']}")
    print(f"导入数量: {report['imports_count']}")
    print()
    
    print("📊 大型函数 (>50行):")
    for func in report['large_functions'][:10]:
        print(f"  - {func['name']}: {func['lines']}行 (复杂度: {func['complexity']})")
    
    print()
    print("🔥 复杂函数 (复杂度>10):")
    for func in report['complex_functions'][:10]:
        print(f"  - {func['name']}: 复杂度{func['complexity']} ({func['lines']}行)")
        
    print()
    print("🔄 重复函数名:")
    for dup in report['duplicates']:
        print(f"  - {dup}")
        
    return report

if __name__ == "__main__":
    analyze_main_file()
