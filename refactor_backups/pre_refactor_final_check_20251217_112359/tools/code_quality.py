#!/usr/bin/env python3
"""
代码质量检查工具
分析代码质量指标和改进建议
"""

import os
import sys
import ast
from pathlib import Path
from collections import defaultdict

class CodeQualityAnalyzer:
    """代码质量分析器"""
    
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.src_dir = self.project_root / "src"
        self.stats = defaultdict(int)
        self.issues = []
    
    def analyze(self):
        """执行完整的代码质量分析"""
        print("=" * 60)
        print("  RAG Pro Max 代码质量分析")
        print("=" * 60)
        
        # 分析所有 Python 文件
        py_files = list(self.src_dir.rglob("*.py"))
        py_files = [f for f in py_files if not f.name.startswith("__")]
        
        print(f"\n📊 项目统计:")
        print(f"Python 文件数: {len(py_files)}")
        
        total_lines = 0
        total_functions = 0
        total_classes = 0
        
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = len(content.splitlines())
                    total_lines += lines
                    
                    # AST 分析
                    tree = ast.parse(content)
                    functions = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
                    classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
                    
                    total_functions += functions
                    total_classes += classes
                    
                    # 检查文件质量
                    self._check_file_quality(py_file, content, lines, functions, classes)
                    
            except Exception as e:
                self.issues.append(f"❌ 无法分析 {py_file.name}: {e}")
        
        print(f"总代码行数: {total_lines:,}")
        print(f"总函数数: {total_functions}")
        print(f"总类数: {total_classes}")
        
        # 显示质量指标
        self._show_quality_metrics()
        
        # 显示问题和建议
        self._show_issues_and_suggestions()
        
        return len(self.issues) == 0
    
    def _check_file_quality(self, file_path, content, lines, functions, classes):
        """检查单个文件的质量"""
        rel_path = file_path.relative_to(self.src_dir)
        
        # 检查文件大小
        if lines > 500:
            self.issues.append(f"⚠️ {rel_path}: 文件过大 ({lines} 行)")
        elif lines > 300:
            self.stats['large_files'] += 1
        
        # 检查函数密度
        if lines > 50 and functions == 0:
            self.issues.append(f"⚠️ {rel_path}: 缺少函数定义")
        
        # 检查文档字符串
        if '"""' not in content and "'''" not in content:
            self.issues.append(f"⚠️ {rel_path}: 缺少文档字符串")
        
        # 检查导入语句
        import_lines = [line for line in content.splitlines() if line.strip().startswith('import ') or line.strip().startswith('from ')]
        if len(import_lines) > 20:
            self.issues.append(f"⚠️ {rel_path}: 导入语句过多 ({len(import_lines)} 个)")
        
        # 更新统计
        self.stats['total_files'] += 1
        self.stats['total_lines'] += lines
        self.stats['total_functions'] += functions
        self.stats['total_classes'] += classes
    
    def _show_quality_metrics(self):
        """显示质量指标"""
        print(f"\n📈 质量指标:")
        
        avg_lines_per_file = self.stats['total_lines'] / self.stats['total_files'] if self.stats['total_files'] > 0 else 0
        avg_functions_per_file = self.stats['total_functions'] / self.stats['total_files'] if self.stats['total_files'] > 0 else 0
        
        print(f"平均文件大小: {avg_lines_per_file:.1f} 行")
        print(f"平均函数数/文件: {avg_functions_per_file:.1f}")
        
        # 质量评分
        quality_score = 100
        if avg_lines_per_file > 300:
            quality_score -= 10
        if len(self.issues) > 10:
            quality_score -= 20
        if self.stats['large_files'] > 5:
            quality_score -= 15
        
        quality_score = max(0, quality_score)
        
        print(f"代码质量评分: {quality_score}/100")
        
        if quality_score >= 90:
            print("🎉 代码质量优秀！")
        elif quality_score >= 80:
            print("✅ 代码质量良好")
        elif quality_score >= 70:
            print("⚠️ 代码质量一般，需要改进")
        else:
            print("❌ 代码质量较差，需要重构")
    
    def _show_issues_and_suggestions(self):
        """显示问题和改进建议"""
        if self.issues:
            print(f"\n⚠️ 发现的问题 ({len(self.issues)} 个):")
            for issue in self.issues[:10]:  # 只显示前10个
                print(f"  {issue}")
            if len(self.issues) > 10:
                print(f"  ... 还有 {len(self.issues) - 10} 个问题")
        
        print(f"\n💡 改进建议:")
        print("  - 保持文件大小在 300 行以内")
        print("  - 为所有模块添加文档字符串")
        print("  - 减少不必要的导入语句")
        print("  - 使用类和函数组织代码")
        print("  - 遵循 PEP 8 代码规范")
    
    def generate_report(self):
        """生成详细报告"""
        report_path = self.project_root / "docs" / "CODE_QUALITY_REPORT.md"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# 代码质量报告\n\n")
            f.write(f"生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## 统计信息\n\n")
            f.write(f"- 文件数: {self.stats['total_files']}\n")
            f.write(f"- 代码行数: {self.stats['total_lines']:,}\n")
            f.write(f"- 函数数: {self.stats['total_functions']}\n")
            f.write(f"- 类数: {self.stats['total_classes']}\n\n")
            
            if self.issues:
                f.write("## 发现的问题\n\n")
                for issue in self.issues:
                    f.write(f"- {issue}\n")
                f.write("\n")
            
            f.write("## 改进建议\n\n")
            f.write("- 保持文件大小在 300 行以内\n")
            f.write("- 为所有模块添加文档字符串\n")
            f.write("- 减少不必要的导入语句\n")
            f.write("- 使用类和函数组织代码\n")
            f.write("- 遵循 PEP 8 代码规范\n")
        
        print(f"\n📄 详细报告已生成: {report_path}")

def main():
    """主函数"""
    project_root = Path(__file__).parent.parent
    analyzer = CodeQualityAnalyzer(project_root)
    
    success = analyzer.analyze()
    analyzer.generate_report()
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
