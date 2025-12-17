#!/usr/bin/env python3
"""
重构执行工具 - 安全执行重构步骤
"""

import ast
import os
import re
from pathlib import Path
from auto_backup import AutoBackup
from test_validator import TestValidator

class RefactorExecutor:
    def __init__(self):
        self.backup = AutoBackup()
        self.validator = TestValidator()
        self.main_file = Path("src/apppro.py")
        
    def extract_function(self, func_name, target_file):
        """提取函数到新文件"""
        print(f"🔧 提取函数: {func_name} -> {target_file}")
        
        # 1. 创建备份
        self.backup.create_snapshot(f"extract_{func_name}")
        
        # 2. 读取主文件
        with open(self.main_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 3. 解析AST找到函数
        tree = ast.parse(content)
        func_node = None
        func_lines = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                func_node = node
                break
                
        if not func_node:
            print(f"❌ 未找到函数: {func_name}")
            return False
            
        # 4. 提取函数代码
        lines = content.split('\n')
        start_line = func_node.lineno - 1
        end_line = func_node.end_lineno
        
        func_code = '\n'.join(lines[start_line:end_line])
        
        # 5. 创建目标文件
        target_path = Path(target_file)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        if target_path.exists():
            with open(target_path, 'r', encoding='utf-8') as f:
                existing = f.read()
        else:
            existing = '#!/usr/bin/env python3\n"""\n提取的函数模块\n"""\n\n'
            
        # 6. 写入函数
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(existing + '\n' + func_code + '\n')
            
        # 7. 从主文件删除函数
        new_lines = lines[:start_line] + lines[end_line:]
        
        # 8. 添加导入
        import_line = f"from {target_file.replace('/', '.').replace('.py', '')} import {func_name}"
        
        # 找到合适的导入位置
        import_pos = 0
        for i, line in enumerate(new_lines):
            if line.startswith('import ') or line.startswith('from '):
                import_pos = i + 1
                
        new_lines.insert(import_pos, import_line)
        
        # 9. 写回主文件
        with open(self.main_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
            
        print(f"✅ 函数已提取: {func_name}")
        
        # 10. 验证测试
        result = self.validator.validate_current()
        if result['status'] == "FAIL":
            print("❌ 测试失败，回滚...")
            self.rollback_last()
            return False
            
        return True
        
    def create_module(self, module_name, functions):
        """创建新模块并移动多个函数"""
        print(f"📦 创建模块: {module_name}")
        
        # 1. 创建备份
        self.backup.create_snapshot(f"create_module_{module_name}")
        
        success_count = 0
        for func_name in functions:
            if self.extract_function(func_name, f"src/{module_name}.py"):
                success_count += 1
            else:
                print(f"⚠️ 函数提取失败: {func_name}")
                
        print(f"✅ 模块创建完成: {success_count}/{len(functions)} 函数成功")
        return success_count == len(functions)
        
    def rollback_last(self):
        """回滚到最后一个快照"""
        snapshots = self.backup.list_snapshots()
        if snapshots:
            latest = snapshots[0]
            self.backup.restore_snapshot(latest.name)
            print(f"🔄 已回滚到: {latest.name}")
        else:
            print("❌ 没有可用的快照")
            
    def safe_refactor_step(self, step_name, refactor_func):
        """安全执行重构步骤"""
        print(f"\n🚀 执行重构步骤: {step_name}")
        
        # 1. 创建备份
        self.backup.create_snapshot(f"before_{step_name}")
        
        # 2. 执行重构
        try:
            success = refactor_func()
            if not success:
                print(f"❌ 重构步骤失败: {step_name}")
                self.rollback_last()
                return False
        except Exception as e:
            print(f"❌ 重构异常: {e}")
            self.rollback_last()
            return False
            
        # 3. 验证测试
        result = self.validator.validate_current()
        if result['status'] == "FAIL":
            print(f"❌ 测试失败，回滚步骤: {step_name}")
            self.rollback_last()
            return False
            
        print(f"✅ 重构步骤完成: {step_name}")
        return True

def main():
    executor = RefactorExecutor()
    
    import sys
    if len(sys.argv) < 2:
        print("用法:")
        print("  python refactor_executor.py extract <函数名> <目标文件>")
        print("  python refactor_executor.py module <模块名> <函数1> <函数2> ...")
        print("  python refactor_executor.py rollback")
        return
        
    command = sys.argv[1]
    
    if command == "extract":
        func_name = sys.argv[2]
        target_file = sys.argv[3]
        executor.extract_function(func_name, target_file)
    elif command == "module":
        module_name = sys.argv[2]
        functions = sys.argv[3:]
        executor.create_module(module_name, functions)
    elif command == "rollback":
        executor.rollback_last()

if __name__ == "__main__":
    main()
