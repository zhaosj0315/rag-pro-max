#!/usr/bin/env python3
"""
导入依赖分析器 - 检测未使用的导入、重复导入和优化建议
"""

import ast
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

class ImportAnalyzer:
    def __init__(self, src_dir: str):
        self.src_dir = Path(src_dir)
        self.results = {
            'unused_imports': [],
            'duplicate_imports': [],
            'optimization_suggestions': [],
            'summary': {}
        }
    
    def analyze_file(self, file_path: Path) -> Dict:
        """分析单个Python文件的导入"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # 收集所有导入
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({
                            'type': 'import',
                            'module': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno,
                            'full_line': content.split('\n')[node.lineno-1].strip()
                        })
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append({
                            'type': 'from_import',
                            'module': module,
                            'name': alias.name,
                            'alias': alias.asname,
                            'line': node.lineno,
                            'full_line': content.split('\n')[node.lineno-1].strip()
                        })
            
            # 检查使用情况
            unused_imports = []
            for imp in imports:
                if not self._is_import_used(content, imp):
                    unused_imports.append(imp)
            
            # 检查重复导入
            duplicate_imports = self._find_duplicate_imports(imports)
            
            return {
                'file': str(file_path),
                'imports': imports,
                'unused_imports': unused_imports,
                'duplicate_imports': duplicate_imports
            }
            
        except Exception as e:
            return {
                'file': str(file_path),
                'error': str(e),
                'imports': [],
                'unused_imports': [],
                'duplicate_imports': []
            }
    
    def _is_import_used(self, content: str, imp: Dict) -> bool:
        """检查导入是否被使用"""
        if imp['type'] == 'import':
            name = imp['alias'] or imp['module'].split('.')[-1]
        else:  # from_import
            name = imp['alias'] or imp['name']
        
        if name == '*':
            return True  # 无法准确检测 import *
        
        # 移除导入行本身
        lines = content.split('\n')
        content_without_imports = '\n'.join(
            line for i, line in enumerate(lines) 
            if i + 1 != imp['line']
        )
        
        # 检查使用模式
        patterns = [
            rf'\b{re.escape(name)}\b',  # 直接使用
            rf'{re.escape(name)}\.',    # 作为模块使用
            rf'@{re.escape(name)}\b',   # 装饰器
            rf'isinstance\([^,]+,\s*{re.escape(name)}\)',  # isinstance
            rf'issubclass\([^,]+,\s*{re.escape(name)}\)',  # issubclass
        ]
        
        for pattern in patterns:
            if re.search(pattern, content_without_imports):
                return True
        
        return False
    
    def _find_duplicate_imports(self, imports: List[Dict]) -> List[Dict]:
        """查找重复导入"""
        seen = {}
        duplicates = []
        
        for imp in imports:
            key = (imp['type'], imp['module'], imp.get('name', ''))
            if key in seen:
                duplicates.append({
                    'original': seen[key],
                    'duplicate': imp
                })
            else:
                seen[key] = imp
        
        return duplicates
    
    def analyze_all_files(self):
        """分析所有Python文件"""
        python_files = list(self.src_dir.rglob('*.py'))
        
        total_unused = 0
        total_duplicates = 0
        
        for file_path in python_files:
            if '__pycache__' in str(file_path):
                continue
                
            result = self.analyze_file(file_path)
            
            if result['unused_imports']:
                self.results['unused_imports'].append(result)
                total_unused += len(result['unused_imports'])
            
            if result['duplicate_imports']:
                self.results['duplicate_imports'].append(result)
                total_duplicates += len(result['duplicate_imports'])
        
        self.results['summary'] = {
            'total_files': len(python_files),
            'files_with_unused': len(self.results['unused_imports']),
            'files_with_duplicates': len(self.results['duplicate_imports']),
            'total_unused_imports': total_unused,
            'total_duplicate_imports': total_duplicates
        }
        
        self._generate_optimization_suggestions()
    
    def _generate_optimization_suggestions(self):
        """生成优化建议"""
        suggestions = []
        
        # 统计最常见的未使用导入
        unused_modules = defaultdict(int)
        for file_result in self.results['unused_imports']:
            for imp in file_result['unused_imports']:
                module = imp['module']
                unused_modules[module] += 1
        
        if unused_modules:
            top_unused = sorted(unused_modules.items(), key=lambda x: x[1], reverse=True)[:5]
            suggestions.append({
                'type': 'common_unused',
                'description': '最常见的未使用导入模块',
                'data': top_unused
            })
        
        # 检查可以合并的导入
        merge_candidates = self._find_merge_candidates()
        if merge_candidates:
            suggestions.append({
                'type': 'merge_imports',
                'description': '可以合并的导入语句',
                'data': merge_candidates
            })
        
        self.results['optimization_suggestions'] = suggestions
    
    def _find_merge_candidates(self) -> List[Dict]:
        """查找可以合并的导入"""
        candidates = []
        
        for file_result in self.results['unused_imports'] + self.results['duplicate_imports']:
            file_imports = defaultdict(list)
            
            # 按模块分组导入
            for imp in file_result.get('imports', []):
                if imp['type'] == 'from_import':
                    file_imports[imp['module']].append(imp)
            
            # 查找同一模块的多个导入
            for module, imports in file_imports.items():
                if len(imports) > 1:
                    candidates.append({
                        'file': file_result['file'],
                        'module': module,
                        'imports': imports,
                        'suggestion': f"可以合并为: from {module} import {', '.join(imp['name'] for imp in imports)}"
                    })
        
        return candidates
    
    def generate_report(self) -> str:
        """生成详细报告"""
        report = []
        report.append("=" * 80)
        report.append("RAG Pro Max - 导入依赖分析报告")
        report.append("=" * 80)
        
        # 摘要
        summary = self.results['summary']
        report.append(f"\n📊 分析摘要:")
        report.append(f"  • 总文件数: {summary['total_files']}")
        report.append(f"  • 有未使用导入的文件: {summary['files_with_unused']}")
        report.append(f"  • 有重复导入的文件: {summary['files_with_duplicates']}")
        report.append(f"  • 未使用导入总数: {summary['total_unused_imports']}")
        report.append(f"  • 重复导入总数: {summary['total_duplicate_imports']}")
        
        # 未使用导入详情
        if self.results['unused_imports']:
            report.append(f"\n🚫 未使用的导入 ({len(self.results['unused_imports'])} 个文件):")
            report.append("-" * 60)
            
            for file_result in self.results['unused_imports']:
                rel_path = os.path.relpath(file_result['file'], self.src_dir)
                report.append(f"\n📄 {rel_path}")
                
                for imp in file_result['unused_imports']:
                    report.append(f"  ❌ 第{imp['line']}行: {imp['full_line']}")
        
        # 重复导入详情
        if self.results['duplicate_imports']:
            report.append(f"\n🔄 重复导入 ({len(self.results['duplicate_imports'])} 个文件):")
            report.append("-" * 60)
            
            for file_result in self.results['duplicate_imports']:
                rel_path = os.path.relpath(file_result['file'], self.src_dir)
                report.append(f"\n📄 {rel_path}")
                
                for dup in file_result['duplicate_imports']:
                    report.append(f"  🔄 重复导入:")
                    report.append(f"     原始: 第{dup['original']['line']}行: {dup['original']['full_line']}")
                    report.append(f"     重复: 第{dup['duplicate']['line']}行: {dup['duplicate']['full_line']}")
        
        # 优化建议
        if self.results['optimization_suggestions']:
            report.append(f"\n💡 优化建议:")
            report.append("-" * 60)
            
            for suggestion in self.results['optimization_suggestions']:
                report.append(f"\n🔧 {suggestion['description']}:")
                
                if suggestion['type'] == 'common_unused':
                    for module, count in suggestion['data']:
                        report.append(f"  • {module}: {count} 次未使用")
                
                elif suggestion['type'] == 'merge_imports':
                    for candidate in suggestion['data']:
                        rel_path = os.path.relpath(candidate['file'], self.src_dir)
                        report.append(f"  📄 {rel_path}")
                        report.append(f"     {candidate['suggestion']}")
        
        # 清理脚本生成
        report.append(f"\n🧹 自动清理建议:")
        report.append("-" * 60)
        report.append("# 可以使用以下命令清理未使用的导入:")
        report.append("# pip install autoflake")
        report.append("# autoflake --remove-all-unused-imports --in-place --recursive src/")
        
        return "\n".join(report)

def main():
    src_dir = "/Users/zhaosj/Documents/rag-pro-max/src"
    
    print("🔍 开始分析导入依赖...")
    analyzer = ImportAnalyzer(src_dir)
    analyzer.analyze_all_files()
    
    report = analyzer.generate_report()
    print(report)
    
    # 保存报告
    report_file = "/Users/zhaosj/Documents/rag-pro-max/import_analysis_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📝 详细报告已保存到: {report_file}")

if __name__ == "__main__":
    main()