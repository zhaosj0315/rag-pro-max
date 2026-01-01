#!/usr/bin/env python3
"""
严格验证清理的代码是否真的无用
"""

import os
import re
import json
from pathlib import Path

class StrictValidator:
    """严格验证器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / ".cleanup_backup"
        self.false_positives = []
        
    def validate_cleanup(self):
        """严格验证清理结果"""
        print("🔍 开始严格验证清理结果...")
        
        # 1. 检查清理报告
        report_file = self.project_root / "CLEANUP_PHASE2_REPORT.md"
        if not report_file.exists():
            print("❌ 清理报告不存在")
            return False
        
        # 2. 验证每个被清理的导入是否真的未使用
        self._validate_removed_imports()
        
        # 3. 运行语法检查
        self._run_syntax_check()
        
        # 4. 运行功能测试
        self._run_functional_test()
        
        print("✅ 验证完成")
        return len(self.false_positives) == 0
    
    def _validate_removed_imports(self):
        """验证移除的导入是否真的未使用"""
        print("🔍 验证移除的导入...")
        
        # 读取清理报告
        with open("CLEANUP_PHASE2_REPORT.md", 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        # 提取被清理的文件和导入
        cleaned_files = []
        lines = report_content.split('\n')
        current_file = None
        
        for line in lines:
            if line.startswith('### '):
                current_file = line.replace('### ', '').strip()
            elif line.startswith('- 具体导入: '):
                imports = line.replace('- 具体导入: ', '').strip()
                if current_file:
                    cleaned_files.append((current_file, imports))
        
        # 验证每个导入是否真的未使用
        for file_path, imports_str in cleaned_files:
            self._check_imports_in_file(file_path, imports_str)
    
    def _check_imports_in_file(self, file_path: str, imports_str: str):
        """检查文件中的导入是否真的未使用"""
        try:
            # 读取当前文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            # 读取备份文件内容
            backup_path = self.backup_dir / file_path
            if not backup_path.exists():
                print(f"⚠️ 备份文件不存在: {backup_path}")
                return
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_content = f.read()
            
            # 解析被移除的导入
            imports = [imp.strip() for imp in imports_str.split(',')]
            
            for imp in imports:
                # 在备份文件中查找这个导入是否真的被使用
                if self._is_import_actually_used(backup_content, imp):
                    self.false_positives.append({
                        'file': file_path,
                        'import': imp,
                        'reason': '导入可能被使用'
                    })
                    print(f"⚠️ 可能的误删: {file_path} 中的 {imp}")
        
        except Exception as e:
            print(f"❌ 验证失败 {file_path}: {e}")
    
    def _is_import_actually_used(self, content: str, import_name: str) -> bool:
        """检查导入是否真的被使用"""
        # 移除导入语句本身
        lines = content.split('\n')
        content_without_imports = []
        
        for line in lines:
            if not re.match(r'^\s*(import|from)\s+', line):
                content_without_imports.append(line)
        
        clean_content = '\n'.join(content_without_imports)
        
        # 检查是否在代码中使用
        patterns = [
            rf'\b{re.escape(import_name)}\.',  # module.function()
            rf'\b{re.escape(import_name)}\(',  # function()
            rf'\b{re.escape(import_name)}\[',  # module[key]
            rf'={re.escape(import_name)}\b',   # var = module
            rf'\({re.escape(import_name)}\b',  # func(module)
        ]
        
        for pattern in patterns:
            if re.search(pattern, clean_content):
                return True
        
        return False
    
    def _run_syntax_check(self):
        """运行语法检查"""
        print("🔍 运行语法检查...")
        
        python_files = [
            "src/apppro.py",
            "src/chat_utils_improved.py", 
            "src/file_processor.py",
            "src/rag_engine.py"
        ]
        
        for file_path in python_files:
            result = os.system(f"python3 -m py_compile {file_path}")
            if result != 0:
                print(f"❌ 语法错误: {file_path}")
                self.false_positives.append({
                    'file': file_path,
                    'reason': '语法错误'
                })
            else:
                print(f"✅ 语法正确: {file_path}")
    
    def _run_functional_test(self):
        """运行功能测试"""
        print("🔍 运行功能测试...")
        
        # 测试主要模块是否可以导入
        test_imports = [
            "from src.apppro import *",
            "from src.file_processor import FileProcessor",
            "from src.rag_engine import RAGEngine"
        ]
        
        for test_import in test_imports:
            try:
                exec(test_import)
                print(f"✅ 导入成功: {test_import}")
            except Exception as e:
                print(f"❌ 导入失败: {test_import} - {e}")
                self.false_positives.append({
                    'import': test_import,
                    'reason': f'导入失败: {e}'
                })
    
    def generate_validation_report(self):
        """生成验证报告"""
        report_content = f"""# 严格验证报告

## 📊 验证结果

- **验证状态**: {'✅ 通过' if len(self.false_positives) == 0 else '❌ 发现问题'}
- **发现问题**: {len(self.false_positives)} 个

## 🔍 详细结果

"""
        
        if len(self.false_positives) == 0:
            report_content += "✅ 所有清理都是安全的，没有发现误删的代码。\n"
        else:
            report_content += "⚠️ 发现以下可能的问题:\n\n"
            for issue in self.false_positives:
                report_content += f"- **文件**: {issue.get('file', 'N/A')}\n"
                report_content += f"  **问题**: {issue['reason']}\n"
                if 'import' in issue:
                    report_content += f"  **导入**: {issue['import']}\n"
                report_content += "\n"
        
        # 保存报告
        with open("STRICT_VALIDATION_REPORT.md", 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📄 验证报告已保存: STRICT_VALIDATION_REPORT.md")

def main():
    validator = StrictValidator()
    is_valid = validator.validate_cleanup()
    validator.generate_validation_report()
    
    if is_valid:
        print("\n✅ 验证通过！所有清理都是安全的。")
    else:
        print(f"\n⚠️ 发现 {len(validator.false_positives)} 个潜在问题，请查看验证报告。")

if __name__ == "__main__":
    main()
