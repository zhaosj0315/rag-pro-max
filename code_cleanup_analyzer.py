#!/usr/bin/env python3
"""
代码清理分析器 - Phase 1
扫描项目中的废弃代码、未使用函数、重复逻辑
"""

import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import json

class CodeCleanupAnalyzer:
    """代码清理分析器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.src_dir = self.project_root / "src"
        self.analysis_results = {
            'unused_functions': [],
            'unused_imports': [],
            'duplicate_functions': [],
            'commented_code': [],
            'large_functions': [],
            'summary': {}
        }
    
    def analyze_project(self):
        """分析整个项目"""
        print("🔍 开始代码清理分析...")
        
        # 1. 扫描所有Python文件
        python_files = list(self.src_dir.rglob("*.py"))
        print(f"📁 找到 {len(python_files)} 个Python文件")
        
        # 2. 分析未使用的函数
        self._analyze_unused_functions(python_files)
        
        # 3. 分析未使用的导入
        self._analyze_unused_imports(python_files)
        
        # 4. 检测重复函数
        self._detect_duplicate_functions(python_files)
        
        # 5. 检测注释代码
        self._detect_commented_code(python_files)
        
        # 6. 检测过大函数
        self._detect_large_functions(python_files)
        
        # 7. 生成分析报告
        self._generate_report()
        
        print("✅ 代码清理分析完成！")
    
    def _analyze_unused_functions(self, python_files: List[Path]):
        """分析未使用的函数"""
        print("🔍 分析未使用的函数...")
        
        # 收集所有函数定义
        all_functions = {}
        function_calls = set()
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 解析AST
                tree = ast.parse(content)
                
                # 收集函数定义
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_name = node.name
                        if not func_name.startswith('_'):  # 跳过私有函数
                            all_functions[func_name] = str(file_path)
                
                # 收集函数调用
                for match in re.finditer(r'(\w+)\s*\(', content):
                    function_calls.add(match.group(1))
                    
            except Exception as e:
                print(f"⚠️ 分析文件失败: {file_path} - {e}")
        
        # 找出未使用的函数
        unused_functions = []
        for func_name, file_path in all_functions.items():
            if func_name not in function_calls:
                unused_functions.append({
                    'function': func_name,
                    'file': file_path,
                    'type': 'unused_function'
                })
        
        self.analysis_results['unused_functions'] = unused_functions
        print(f"📊 发现 {len(unused_functions)} 个可能未使用的函数")
    
    def _analyze_unused_imports(self, python_files: List[Path]):
        """分析未使用的导入"""
        print("🔍 分析未使用的导入...")
        
        unused_imports = []
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找import语句
                import_lines = []
                for i, line in enumerate(content.split('\n')):
                    if re.match(r'^\s*(import|from)\s+', line):
                        import_lines.append((i+1, line.strip()))
                
                # 检查每个导入是否被使用
                for line_num, import_line in import_lines:
                    if 'import' in import_line:
                        # 提取导入的模块名
                        if import_line.startswith('from'):
                            match = re.search(r'from\s+[\w.]+\s+import\s+([\w,\s]+)', import_line)
                            if match:
                                imports = [imp.strip() for imp in match.group(1).split(',')]
                        else:
                            match = re.search(r'import\s+([\w.]+)', import_line)
                            if match:
                                imports = [match.group(1).split('.')[-1]]
                        
                        # 检查是否在代码中使用
                        for imp in imports:
                            if imp not in content.replace(import_line, ''):
                                unused_imports.append({
                                    'import': imp,
                                    'line': line_num,
                                    'file': str(file_path),
                                    'full_line': import_line
                                })
                                
            except Exception as e:
                print(f"⚠️ 分析导入失败: {file_path} - {e}")
        
        self.analysis_results['unused_imports'] = unused_imports
        print(f"📊 发现 {len(unused_imports)} 个可能未使用的导入")
    
    def _detect_duplicate_functions(self, python_files: List[Path]):
        """检测重复函数"""
        print("🔍 检测重复函数...")
        
        function_signatures = {}
        duplicates = []
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 查找函数定义
                for match in re.finditer(r'def\s+(\w+)\s*\([^)]*\):', content):
                    func_name = match.group(1)
                    
                    if func_name in function_signatures:
                        duplicates.append({
                            'function': func_name,
                            'files': [function_signatures[func_name], str(file_path)],
                            'type': 'duplicate_function'
                        })
                    else:
                        function_signatures[func_name] = str(file_path)
                        
            except Exception as e:
                print(f"⚠️ 检测重复失败: {file_path} - {e}")
        
        self.analysis_results['duplicate_functions'] = duplicates
        print(f"📊 发现 {len(duplicates)} 个重复函数")
    
    def _detect_commented_code(self, python_files: List[Path]):
        """检测注释代码"""
        print("🔍 检测注释代码...")
        
        commented_code = []
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for i, line in enumerate(lines):
                    # 检测注释掉的代码行
                    if re.match(r'^\s*#\s*(def|class|import|if|for|while|try)', line):
                        commented_code.append({
                            'file': str(file_path),
                            'line': i+1,
                            'content': line.strip(),
                            'type': 'commented_code'
                        })
                        
            except Exception as e:
                print(f"⚠️ 检测注释代码失败: {file_path} - {e}")
        
        self.analysis_results['commented_code'] = commented_code
        print(f"📊 发现 {len(commented_code)} 行注释代码")
    
    def _detect_large_functions(self, python_files: List[Path]):
        """检测过大函数"""
        print("🔍 检测过大函数...")
        
        large_functions = []
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # 计算函数行数
                        func_lines = node.end_lineno - node.lineno + 1
                        if func_lines > 50:  # 超过50行的函数
                            large_functions.append({
                                'function': node.name,
                                'file': str(file_path),
                                'lines': func_lines,
                                'start_line': node.lineno,
                                'type': 'large_function'
                            })
                            
            except Exception as e:
                print(f"⚠️ 检测大函数失败: {file_path} - {e}")
        
        self.analysis_results['large_functions'] = large_functions
        print(f"📊 发现 {len(large_functions)} 个过大函数")
    
    def _generate_report(self):
        """生成分析报告"""
        print("📋 生成分析报告...")
        
        # 统计信息
        summary = {
            'total_files': len(list(self.src_dir.rglob("*.py"))),
            'unused_functions_count': len(self.analysis_results['unused_functions']),
            'unused_imports_count': len(self.analysis_results['unused_imports']),
            'duplicate_functions_count': len(self.analysis_results['duplicate_functions']),
            'commented_code_count': len(self.analysis_results['commented_code']),
            'large_functions_count': len(self.analysis_results['large_functions'])
        }
        
        self.analysis_results['summary'] = summary
        
        # 保存到文件
        report_file = self.project_root / "code_cleanup_analysis.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)
        
        # 生成可读报告
        self._generate_readable_report()
        
        print(f"📄 分析报告已保存: {report_file}")
    
    def _generate_readable_report(self):
        """生成可读的分析报告"""
        
        report_content = f"""# 代码清理分析报告

## 📊 分析概览

- **总文件数**: {self.analysis_results['summary']['total_files']}
- **未使用函数**: {self.analysis_results['summary']['unused_functions_count']} 个
- **未使用导入**: {self.analysis_results['summary']['unused_imports_count']} 个
- **重复函数**: {self.analysis_results['summary']['duplicate_functions_count']} 个
- **注释代码**: {self.analysis_results['summary']['commented_code_count']} 行
- **过大函数**: {self.analysis_results['summary']['large_functions_count']} 个

## 🗑️ 建议清理项目

### 未使用函数
"""
        
        for item in self.analysis_results['unused_functions'][:10]:  # 只显示前10个
            report_content += f"- `{item['function']}()` in {item['file']}\n"
        
        report_content += f"\n### 未使用导入\n"
        for item in self.analysis_results['unused_imports'][:10]:
            report_content += f"- `{item['import']}` in {item['file']}:{item['line']}\n"
        
        report_content += f"\n### 重复函数\n"
        for item in self.analysis_results['duplicate_functions'][:10]:
            report_content += f"- `{item['function']}()` in {', '.join(item['files'])}\n"
        
        # 保存可读报告
        report_file = self.project_root / "CODE_CLEANUP_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📄 可读报告已保存: {report_file}")

def main():
    """主函数"""
    analyzer = CodeCleanupAnalyzer()
    analyzer.analyze_project()
    
    print("\n🎯 下一步建议:")
    print("1. 查看 CODE_CLEANUP_REPORT.md 了解详细分析结果")
    print("2. 查看 code_cleanup_analysis.json 获取完整数据")
    print("3. 开始Phase 2: 安全清理阶段")

if __name__ == "__main__":
    main()
