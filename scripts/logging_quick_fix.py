#!/usr/bin/env python3
"""
日志管理快速修复工具
自动为关键函数添加性能监控和日志记录
"""

import re
import os
from pathlib import Path
from typing import List, Dict

class LoggingQuickFix:
    def __init__(self, src_dir: str = "src"):
        self.src_dir = Path(src_dir)
        self.fixes_applied = []
        
    def should_add_monitoring(self, func_name: str, file_content: str) -> bool:
        """判断函数是否需要添加监控"""
        critical_keywords = ['process', 'handle', 'create', 'build', 'load', 'save', 'query', 'search']
        
        # 检查函数名
        for keyword in critical_keywords:
            if keyword in func_name.lower():
                return True
        return False
    
    def has_existing_monitoring(self, func_content: str) -> bool:
        """检查函数是否已有监控"""
        monitoring_patterns = [
            r'logger\.timer\(',
            r'with.*timer',
            r'start_timer',
            r'end_timer',
            r'st\.status\(',
            r'st\.progress\('
        ]
        
        for pattern in monitoring_patterns:
            if re.search(pattern, func_content):
                return True
        return False
    
    def add_logger_import(self, file_content: str) -> str:
        """添加 LogManager 导入"""
        if 'from src.app_logging.log_manager import LogManager' in file_content:
            return file_content
            
        # 找到合适的位置插入导入
        lines = file_content.split('\n')
        import_index = 0
        
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_index = i + 1
            elif line.strip() == '' and import_index > 0:
                break
                
        lines.insert(import_index, 'from src.app_logging.log_manager import LogManager')
        return '\n'.join(lines)
    
    def add_function_monitoring(self, func_match: re.Match, file_content: str) -> str:
        """为函数添加监控"""
        func_name = func_match.group(1)
        func_start = func_match.start()
        func_end = func_match.end()
        
        # 获取函数体
        lines = file_content[func_end:].split('\n')
        indent = '    '  # 假设使用4空格缩进
        
        # 检查是否已有 logger 实例
        if 'logger = LogManager()' not in file_content:
            # 在函数开始添加 logger 实例和计时
            monitoring_code = f'''
{indent}logger = LogManager()
{indent}
{indent}with logger.timer("{func_name}"):'''
        else:
            monitoring_code = f'''
{indent}with logger.timer("{func_name}"):'''
        
        # 找到函数体开始位置
        for i, line in enumerate(lines):
            if line.strip() and not line.strip().startswith('"""') and not line.strip().startswith("'''"):
                # 在第一行实际代码前插入监控
                lines.insert(i, monitoring_code)
                # 缩进后续代码
                for j in range(i + 1, len(lines)):
                    if lines[j].strip():
                        lines[j] = indent + lines[j]
                break
        
        return file_content[:func_end] + '\n'.join(lines)
    
    def fix_file(self, file_path: Path) -> Dict:
        """修复单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            fixes_count = 0
            
            # 1. 替换 logging 导入为 LogManager
            if 'import logging' in content and 'LogManager' not in content:
                content = re.sub(r'import logging', 
                                'from src.app_logging.log_manager import LogManager', 
                                content)
                fixes_count += 1
            
            # 2. 添加 LogManager 导入（如果需要）
            func_pattern = r'def\s+(\w*(?:process|handle|create|build|load|save|query|search)\w*)\s*\('
            if re.search(func_pattern, content, re.IGNORECASE):
                content = self.add_logger_import(content)
            
            # 3. 为关键函数添加监控（简化版本 - 仅添加日志记录）
            def add_logging(match):
                func_name = match.group(1)
                if self.should_add_monitoring(func_name, content):
                    # 简单添加日志记录而不是完整的计时器
                    return f'{match.group(0)}\n    logger = LogManager()\n    logger.info("开始执行", stage="{func_name}")'
                return match.group(0)
            
            new_content = re.sub(func_pattern, add_logging, content, flags=re.IGNORECASE)
            if new_content != content:
                fixes_count += 1
                content = new_content
            
            # 如果有修改，写回文件
            if content != original_content:
                # 创建备份
                backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                # 写入修改后的内容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return {
                    'path': str(file_path),
                    'fixes': fixes_count,
                    'backup': str(backup_path),
                    'success': True
                }
            
            return {'path': str(file_path), 'fixes': 0, 'success': True}
            
        except Exception as e:
            return {'path': str(file_path), 'error': str(e), 'success': False}
    
    def run_fixes(self, dry_run: bool = True) -> Dict:
        """运行修复"""
        print(f"🔧 开始日志管理快速修复 ({'预览模式' if dry_run else '实际修复'})")
        
        results = {
            'total_files': 0,
            'fixed_files': 0,
            'total_fixes': 0,
            'errors': [],
            'details': []
        }
        
        for py_file in self.src_dir.rglob("*.py"):
            if '__pycache__' in str(py_file) or 'test' in str(py_file):
                continue
                
            results['total_files'] += 1
            
            if not dry_run:
                result = self.fix_file(py_file)
                results['details'].append(result)
                
                if result['success']:
                    if result.get('fixes', 0) > 0:
                        results['fixed_files'] += 1
                        results['total_fixes'] += result['fixes']
                        print(f"✅ {py_file}: {result['fixes']} 处修复")
                else:
                    results['errors'].append(result)
                    print(f"❌ {py_file}: {result['error']}")
            else:
                # 预览模式：只检查不修改
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 检查是否需要修复
                    needs_fix = False
                    if 'import logging' in content and 'LogManager' not in content:
                        needs_fix = True
                        
                    func_pattern = r'def\s+(\w*(?:process|handle|create|build|load|save|query|search)\w*)\s*\('
                    if re.search(func_pattern, content, re.IGNORECASE):
                        needs_fix = True
                    
                    if needs_fix:
                        results['fixed_files'] += 1
                        print(f"📋 {py_file}: 需要修复")
                        
                except Exception as e:
                    print(f"⚠️ {py_file}: 检查失败 - {e}")
        
        return results
    
    def print_summary(self, results: Dict, dry_run: bool):
        """打印修复摘要"""
        print(f"\n📊 修复摘要")
        print("=" * 30)
        print(f"📁 检查文件: {results['total_files']}")
        print(f"🔧 {'需要修复' if dry_run else '已修复'}: {results['fixed_files']}")
        
        if not dry_run:
            print(f"✅ 总修复数: {results['total_fixes']}")
            if results['errors']:
                print(f"❌ 错误数量: {len(results['errors'])}")

def main():
    """主函数"""
    import sys
    
    print("🚀 RAG Pro Max 日志管理快速修复工具")
    print("=" * 50)
    
    # 检查参数
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    
    if dry_run:
        print("🔍 预览模式：只检查不修改文件")
    else:
        print("⚠️ 实际修复模式：将修改文件（会创建备份）")
        confirm = input("确认继续？(y/N): ")
        if confirm.lower() != 'y':
            print("❌ 操作已取消")
            return
    
    fixer = LoggingQuickFix()
    results = fixer.run_fixes(dry_run=dry_run)
    fixer.print_summary(results, dry_run)
    
    if dry_run:
        print(f"\n💡 要执行实际修复，请运行: python {sys.argv[0]}")
    else:
        print(f"\n✅ 修复完成！备份文件已保存为 .backup")
        print(f"📋 建议运行测试确认修复效果")

if __name__ == "__main__":
    main()
