#!/usr/bin/env python3
"""
性能监控覆盖率检查脚本
检查关键函数是否有性能监控和计时
"""

import ast
import os
from pathlib import Path
from typing import List, Dict, Tuple

class PerformanceMonitorChecker:
    def __init__(self, src_dir: str = "src"):
        self.src_dir = Path(src_dir)
        self.monitored_functions = []
        self.unmonitored_functions = []
        self.critical_functions = []
        
    def is_critical_function(self, func_name: str, file_path: str) -> bool:
        """判断是否为关键函数（需要性能监控）"""
        critical_keywords = [
            'process', 'handle', 'create', 'build', 'load', 'save',
            'query', 'search', 'index', 'vectorize', 'crawl', 'upload'
        ]
        
        # 检查函数名
        for keyword in critical_keywords:
            if keyword in func_name.lower():
                return True
                
        # 检查文件路径（某些关键模块的所有函数都应监控）
        critical_modules = ['processor', 'engine', 'builder', 'crawler']
        for module in critical_modules:
            if module in str(file_path).lower():
                return True
                
        return False
    
    def has_timer_usage(self, node: ast.FunctionDef) -> bool:
        """检查函数是否使用了计时器"""
        for child in ast.walk(node):
            # 检查 with timer() 语句
            if isinstance(child, ast.With):
                for item in child.items:
                    if isinstance(item.context_expr, ast.Call):
                        if hasattr(item.context_expr.func, 'attr') and 'timer' in item.context_expr.func.attr:
                            return True
                        if hasattr(item.context_expr.func, 'id') and 'timer' in item.context_expr.func.id:
                            return True
            
            # 检查 start_timer/end_timer 调用
            if isinstance(child, ast.Call):
                if hasattr(child.func, 'attr'):
                    if child.func.attr in ['start_timer', 'end_timer', 'timer']:
                        return True
                        
        return False
    
    def has_progress_tracking(self, node: ast.FunctionDef) -> bool:
        """检查函数是否有进度跟踪"""
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if hasattr(child.func, 'attr'):
                    if child.func.attr in ['progress_bar', 'progress', 'status']:
                        return True
                # 检查 st.progress 调用
                if (hasattr(child.func, 'value') and 
                    hasattr(child.func.value, 'id') and 
                    child.func.value.id == 'st' and
                    hasattr(child.func, 'attr') and
                    child.func.attr in ['progress', 'status']):
                    return True
        return False
    
    def analyze_file(self, file_path: Path) -> Dict:
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            file_stats = {
                'path': str(file_path),
                'functions': [],
                'monitored_count': 0,
                'critical_count': 0
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'is_critical': self.is_critical_function(node.name, file_path),
                        'has_timer': self.has_timer_usage(node),
                        'has_progress': self.has_progress_tracking(node)
                    }
                    
                    file_stats['functions'].append(func_info)
                    
                    if func_info['is_critical']:
                        file_stats['critical_count'] += 1
                        
                        if func_info['has_timer'] or func_info['has_progress']:
                            file_stats['monitored_count'] += 1
                            self.monitored_functions.append(f"{file_path}:{node.name}")
                        else:
                            self.unmonitored_functions.append(f"{file_path}:{node.name}")
                            
            return file_stats
            
        except Exception as e:
            print(f"⚠️ 分析文件失败 {file_path}: {e}")
            return {'path': str(file_path), 'functions': [], 'error': str(e)}
    
    def run_analysis(self) -> Dict:
        """运行完整分析"""
        print("🔍 开始性能监控覆盖率分析...")
        
        all_stats = []
        total_functions = 0
        total_critical = 0
        total_monitored = 0
        
        for py_file in self.src_dir.rglob("*.py"):
            if '__pycache__' in str(py_file):
                continue
                
            stats = self.analyze_file(py_file)
            if 'error' not in stats:
                all_stats.append(stats)
                total_functions += len(stats['functions'])
                total_critical += stats['critical_count']
                total_monitored += stats['monitored_count']
        
        # 计算覆盖率
        coverage_rate = (total_monitored / total_critical * 100) if total_critical > 0 else 0
        
        return {
            'files': all_stats,
            'summary': {
                'total_functions': total_functions,
                'critical_functions': total_critical,
                'monitored_functions': total_monitored,
                'coverage_rate': coverage_rate
            }
        }
    
    def print_report(self, results: Dict):
        """打印分析报告"""
        summary = results['summary']
        
        print("\n📊 性能监控覆盖率报告")
        print("=" * 40)
        print(f"📁 总函数数量: {summary['total_functions']}")
        print(f"🎯 关键函数数量: {summary['critical_functions']}")
        print(f"✅ 已监控函数: {summary['monitored_functions']}")
        print(f"📈 监控覆盖率: {summary['coverage_rate']:.1f}%")
        
        # 评级
        if summary['coverage_rate'] >= 80:
            grade = "🏆 优秀"
        elif summary['coverage_rate'] >= 60:
            grade = "👍 良好"
        elif summary['coverage_rate'] >= 40:
            grade = "⚠️ 一般"
        else:
            grade = "❌ 需要改进"
            
        print(f"🎯 评级: {grade}")
        
        # 显示未监控的关键函数
        if self.unmonitored_functions:
            print(f"\n⚠️ 建议添加性能监控的关键函数 (前10个):")
            for func in self.unmonitored_functions[:10]:
                print(f"  📍 {func}")
                
        # 显示已监控的函数示例
        if self.monitored_functions:
            print(f"\n✅ 已有性能监控的函数示例:")
            for func in self.monitored_functions[:5]:
                print(f"  ✓ {func}")
    
    def generate_improvement_suggestions(self, results: Dict) -> List[str]:
        """生成改进建议"""
        suggestions = []
        summary = results['summary']
        
        if summary['coverage_rate'] < 50:
            suggestions.append("🔧 建议为关键业务函数添加 logger.timer() 计时")
            
        if len(self.unmonitored_functions) > 10:
            suggestions.append("📊 建议为长时间操作添加进度显示")
            
        # 分析具体模块
        module_stats = {}
        for file_stat in results['files']:
            module_name = Path(file_stat['path']).parent.name
            if module_name not in module_stats:
                module_stats[module_name] = {'critical': 0, 'monitored': 0}
            module_stats[module_name]['critical'] += file_stat['critical_count']
            module_stats[module_name]['monitored'] += file_stat['monitored_count']
        
        for module, stats in module_stats.items():
            if stats['critical'] > 0:
                coverage = stats['monitored'] / stats['critical'] * 100
                if coverage < 30:
                    suggestions.append(f"🎯 {module} 模块监控覆盖率较低 ({coverage:.1f}%)，建议重点优化")
        
        return suggestions

def main():
    """主函数"""
    print("🚀 RAG Pro Max 性能监控检查工具")
    print("=" * 50)
    
    checker = PerformanceMonitorChecker()
    results = checker.run_analysis()
    checker.print_report(results)
    
    # 改进建议
    suggestions = checker.generate_improvement_suggestions(results)
    if suggestions:
        print(f"\n💡 改进建议:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")
    
    print(f"\n📋 详细规范请参考: LOGGING_AND_NOTIFICATION_STANDARD.md")

if __name__ == "__main__":
    main()
