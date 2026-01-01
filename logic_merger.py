#!/usr/bin/env python3
"""
逻辑合并清理器 - Phase 3
合并重复的函数和相似的逻辑
"""

import os
import ast
import re
import json
from pathlib import Path
from typing import List, Dict, Set

class LogicMerger:
    """逻辑合并清理器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.analysis_file = self.project_root / "code_cleanup_analysis.json"
        self.backup_dir = self.project_root / ".cleanup_backup_phase3"
        self.merged_functions = []
        
        # 加载分析结果
        with open(self.analysis_file, 'r', encoding='utf-8') as f:
            self.analysis_data = json.load(f)
    
    def merge_logic(self):
        """执行逻辑合并"""
        print("🔄 开始逻辑合并清理...")
        
        # 创建备份目录
        self.backup_dir.mkdir(exist_ok=True)
        
        # 1. 分析重复函数的具体情况
        self._analyze_duplicate_functions()
        
        # 2. 合并简单的重复函数
        self._merge_simple_duplicates()
        
        # 3. 生成合并报告
        self._generate_merge_report()
        
        print("✅ 逻辑合并完成！")
    
    def _analyze_duplicate_functions(self):
        """分析重复函数的具体情况"""
        print("🔍 分析重复函数...")
        
        # 按函数名分组
        function_groups = {}
        for item in self.analysis_data['duplicate_functions']:
            func_name = item['function']
            if func_name not in function_groups:
                function_groups[func_name] = []
            function_groups[func_name].append(item)
        
        # 分析每组函数
        for func_name, items in function_groups.items():
            print(f"📋 函数 '{func_name}' 在 {len(items)} 个位置重复")
            
            # 特殊处理常见的重复函数
            if func_name == '__init__':
                self._analyze_init_functions(items)
            elif func_name == 'update_status':
                self._analyze_update_status_functions(items)
            elif func_name.endswith('_fragment'):
                self._analyze_fragment_functions(items)
    
    def _analyze_init_functions(self, items):
        """分析__init__函数的重复情况"""
        print("🔍 分析__init__函数重复...")
        
        # __init__函数通常是正常的，每个类都有自己的初始化
        # 这里主要检查是否有真正的重复逻辑
        for item in items:
            files = item['files']
            if len(files) >= 2:
                # 检查是否在同一个文件中重复定义
                if files[0] == files[1]:
                    print(f"⚠️ 发现同文件内重复__init__: {files[0]}")
    
    def _analyze_update_status_functions(self, items):
        """分析update_status函数的重复情况"""
        print("🔍 分析update_status函数重复...")
        
        # update_status函数可能确实有重复逻辑，需要合并
        for item in items:
            files = item['files']
            if len(files) >= 2:
                print(f"📝 可能需要合并的update_status: {files}")
                self._check_function_similarity(files, 'update_status')
    
    def _analyze_fragment_functions(self, items):
        """分析fragment函数的重复情况"""
        print("🔍 分析fragment函数重复...")
        
        # fragment函数可能有相似的UI逻辑
        for item in items:
            files = item['files']
            if len(files) >= 2:
                print(f"📝 可能需要合并的fragment: {files}")
    
    def _check_function_similarity(self, files: List[str], func_name: str):
        """检查函数的相似性"""
        try:
            function_contents = []
            
            for file_path in files:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 提取函数内容
                escaped_name = re.escape(func_name)
                pattern = rf'def\s+{escaped_name}\s*\([^)]*\):.*?(?=\n\s*def|\n\s*class|\Z)'
                matches = re.findall(pattern, content, re.DOTALL)
                if matches:
                    function_contents.append((file_path, matches[0]))
            
            # 比较函数内容的相似性
            if len(function_contents) >= 2:
                content1 = function_contents[0][1]
                content2 = function_contents[1][1]
                
                # 简单的相似性检查（去除空白后比较）
                clean_content1 = re.sub(r'\s+', ' ', content1).strip()
                clean_content2 = re.sub(r'\s+', ' ', content2).strip()
                
                if clean_content1 == clean_content2:
                    print(f"🎯 发现完全相同的函数: {func_name}")
                    return True
                elif len(clean_content1) > 0 and len(clean_content2) > 0:
                    # 计算相似度
                    similarity = self._calculate_similarity(clean_content1, clean_content2)
                    if similarity > 0.8:
                        print(f"🎯 发现高度相似的函数: {func_name} (相似度: {similarity:.2f})")
                        return True
        
        except Exception as e:
            print(f"⚠️ 检查函数相似性失败: {e}")
        
        return False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        # 简单的基于字符的相似度计算
        if not text1 or not text2:
            return 0.0
        
        # 使用最长公共子序列
        def lcs_length(s1, s2):
            m, n = len(s1), len(s2)
            dp = [[0] * (n + 1) for _ in range(m + 1)]
            
            for i in range(1, m + 1):
                for j in range(1, n + 1):
                    if s1[i-1] == s2[j-1]:
                        dp[i][j] = dp[i-1][j-1] + 1
                    else:
                        dp[i][j] = max(dp[i-1][j], dp[i][j-1])
            
            return dp[m][n]
        
        lcs_len = lcs_length(text1, text2)
        max_len = max(len(text1), len(text2))
        
        return lcs_len / max_len if max_len > 0 else 0.0
    
    def _merge_simple_duplicates(self):
        """合并简单的重复函数"""
        print("🔄 合并简单的重复函数...")
        
        # 这里实现保守的合并策略
        # 只合并明显相同的函数，避免破坏功能
        
        # 示例：合并完全相同的工具函数
        self._merge_identical_utility_functions()
    
    def _merge_identical_utility_functions(self):
        """合并完全相同的工具函数"""
        print("🔧 合并完全相同的工具函数...")
        
        # 这里可以实现具体的合并逻辑
        # 但为了安全起见，先生成报告，让用户手动确认
        pass
    
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
    
    def _generate_merge_report(self):
        """生成合并报告"""
        report_content = f"""# 逻辑合并报告 - Phase 3

## 📊 分析概览

- **重复函数总数**: {len(self.analysis_data['duplicate_functions'])}
- **已合并函数**: {len(self.merged_functions)}

## 🔍 重复函数分析

### 常见重复函数

"""
        
        # 按函数名统计
        function_counts = {}
        for item in self.analysis_data['duplicate_functions']:
            func_name = item['function']
            function_counts[func_name] = function_counts.get(func_name, 0) + 1
        
        # 显示最常见的重复函数
        sorted_functions = sorted(function_counts.items(), key=lambda x: x[1], reverse=True)
        for func_name, count in sorted_functions[:10]:
            report_content += f"- `{func_name}()`: {count} 次重复\n"
        
        report_content += f"""

## 🎯 建议手动处理的重复函数

### __init__ 函数
- 大多数__init__函数是正常的类初始化，无需合并
- 只有同一文件内的重复定义需要处理

### update_status 函数
- 可能存在真正的重复逻辑
- 建议检查是否可以提取为公共函数

### fragment 函数
- UI组件的fragment函数可能有相似逻辑
- 建议检查是否可以创建通用的UI组件

## 🛠️ 下一步建议

1. **手动检查**: 逐个检查重复函数的实际内容
2. **提取公共逻辑**: 将相同的逻辑提取为公共函数
3. **创建工具类**: 将重复的工具函数整合到工具类中
4. **统一接口**: 为相似功能创建统一的接口

## ⚠️ 注意事项

- 不要盲目合并所有重复函数
- 确保合并后的逻辑符合各自的使用场景
- 保持接口的向后兼容性
- 充分测试合并后的功能
"""
        
        # 保存报告
        report_file = self.project_root / "CLEANUP_PHASE3_REPORT.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📄 合并报告已保存: {report_file}")

def main():
    """主函数"""
    merger = LogicMerger()
    merger.merge_logic()
    
    print("\n🎯 下一步建议:")
    print("1. 查看 CLEANUP_PHASE3_REPORT.md 了解重复函数分析")
    print("2. 手动检查和合并真正重复的逻辑")
    print("3. 创建公共工具函数减少重复")
    print("4. 继续Phase 4: 结构优化")

if __name__ == "__main__":
    main()
