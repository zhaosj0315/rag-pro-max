#!/usr/bin/env python3
"""
代码安全清理器 - Phase 2
安全地清理明显的废弃代码和未使用的导入
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict

class SafeCodeCleaner:
    """安全代码清理器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.analysis_file = self.project_root / "code_cleanup_analysis.json"
        self.backup_dir = self.project_root / ".cleanup_backup"
        self.cleaned_files = []
        
        # 加载分析结果
        with open(self.analysis_file, 'r', encoding='utf-8') as f:
            self.analysis_data = json.load(f)
    
    def safe_cleanup(self):
        """执行安全清理"""
        print("🧹 开始安全代码清理...")
        
        # 创建备份目录
        self.backup_dir.mkdir(exist_ok=True)
        
        # 1. 清理明显未使用的导入（保守策略）
        self._clean_safe_unused_imports()
        
        # 2. 生成清理报告
        self._generate_cleanup_report()
        
        print("✅ 安全清理完成！")
        print(f"📁 备份文件保存在: {self.backup_dir}")
        print("🧪 请运行测试验证功能正常")
    
    def _clean_safe_unused_imports(self):
        """清理明显安全的未使用导入"""
        print("🔍 清理安全的未使用导入...")
        
        # 定义安全清理的导入类型（保守策略）
        safe_to_remove = {
            'shutil', 'datetime', 'zipfile', 'multiprocessing', 
            'requests', 'json', 'os', 'sys', 'time'
        }
        
        files_to_clean = {}
        
        # 按文件分组未使用的导入
        for item in self.analysis_data['unused_imports']:
            file_path = item['file']
            if file_path not in files_to_clean:
                files_to_clean[file_path] = []
            
            # 只清理安全的导入
            if item['import'] in safe_to_remove:
                files_to_clean[file_path].append(item)
        
        cleaned_count = 0
        
        for file_path, imports_to_remove in files_to_clean.items():
            if len(imports_to_remove) == 0:
                continue
                
            try:
                # 备份原文件
                self._backup_file(file_path)
                
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # 标记要删除的行
                lines_to_remove = set()
                for item in imports_to_remove:
                    line_num = item['line'] - 1  # 转换为0索引
                    if line_num < len(lines):
                        # 验证这一行确实是导入语句
                        line_content = lines[line_num].strip()
                        if ('import' in line_content and 
                            item['import'] in line_content):
                            lines_to_remove.add(line_num)
                
                # 创建新的文件内容
                new_lines = []
                for i, line in enumerate(lines):
                    if i not in lines_to_remove:
                        new_lines.append(line)
                
                # 写回文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                
                cleaned_count += len(lines_to_remove)
                self.cleaned_files.append({
                    'file': file_path,
                    'removed_imports': len(lines_to_remove),
                    'imports': [item['import'] for item in imports_to_remove]
                })
                
                print(f"✅ 清理 {file_path}: 移除 {len(lines_to_remove)} 个导入")
                
            except Exception as e:
                print(f"⚠️ 清理失败 {file_path}: {e}")
        
        print(f"📊 总计清理了 {cleaned_count} 个未使用的导入")
    
    def _backup_file(self, file_path: str):
        """备份文件"""
        source_path = Path(file_path)
        if not source_path.exists():
            return
        
        # 创建备份路径
        relative_path = source_path.relative_to(self.project_root)
        backup_path = self.backup_dir / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 复制文件
        import shutil
        shutil.copy2(source_path, backup_path)
    
    def _generate_cleanup_report(self):
        """生成清理报告"""
        report_content = f"""# 代码清理报告 - Phase 2

## 📊 清理概览

- **清理文件数**: {len(self.cleaned_files)}
- **移除导入总数**: {sum(item['removed_imports'] for item in self.cleaned_files)}

## 🧹 清理详情

"""
        
        for item in self.cleaned_files:
            report_content += f"### {item['file']}\n"
            report_content += f"- 移除导入: {item['removed_imports']} 个\n"
            report_content += f"- 具体导入: {', '.join(item['imports'])}\n\n"
        
        report_content += f"""
## 🔄 回滚说明

如果清理后出现问题，可以从备份恢复：

```bash
# 恢复所有文件
cp -r .cleanup_backup/* .

# 或恢复单个文件
cp .cleanup_backup/src/apppro.py src/apppro.py
```

## 🧪 测试验证

请运行以下测试确保功能正常：

```bash
# 语法检查
python3 -m py_compile src/apppro.py

# 功能测试
python3 tests/factory_test.py

# 启动测试
streamlit run src/apppro.py
```
"""
        
        # 保存报告
        report_file = self.project_root / "CLEANUP_PHASE2_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📄 清理报告已保存: {report_file}")

def main():
    """主函数"""
    cleaner = SafeCodeCleaner()
    cleaner.safe_cleanup()
    
    print("\n🎯 下一步建议:")
    print("1. 运行 python3 -m py_compile src/apppro.py 检查语法")
    print("2. 运行 streamlit run src/apppro.py 测试启动")
    print("3. 如果一切正常，继续Phase 3清理")
    print("4. 如果有问题，从 .cleanup_backup 恢复文件")

if __name__ == "__main__":
    main()
