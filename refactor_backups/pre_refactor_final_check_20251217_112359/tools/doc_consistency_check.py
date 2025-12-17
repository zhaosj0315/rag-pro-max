#!/usr/bin/env python3
"""
文档一致性检查工具
检查所有文档与代码的一致性
"""

import os
import re
import json
from pathlib import Path

class DocumentConsistencyChecker:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.src_dir = self.project_root / "src"
        self.docs_dir = self.project_root / "docs"
        self.tests_dir = self.project_root / "tests"
        
    def check_version_consistency(self):
        """检查版本信息一致性"""
        print("🔍 检查版本信息一致性...")
        
        # 检查README.md中的版本
        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
                
            # 查找版本信息
            version_badge = re.search(r'version-(\d+\.\d+\.\d+)', readme_content)
            version_text = re.search(r'\*\*v(\d+\.\d+\.\d+)', readme_content)
            
            if version_badge and version_text:
                badge_version = version_badge.group(1)
                text_version = version_text.group(1)
                
                if badge_version == text_version:
                    print(f"✅ 版本信息一致: v{badge_version}")
                    return True
                else:
                    print(f"❌ 版本信息不一致: badge={badge_version}, text={text_version}")
                    return False
            else:
                print("❌ 未找到版本信息")
                return False
        
        print("❌ README.md 不存在")
        return False
    
    def check_module_count(self):
        """检查模块数量一致性"""
        print("\n🔍 检查模块数量一致性...")
        
        # 统计实际Python文件数量
        py_files = list(self.src_dir.glob("**/*.py"))
        actual_count = len(py_files)
        
        # 检查README中声明的数量
        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
                
            # 查找文件数量声明
            file_count_match = re.search(r'(\d+)个Python文件', readme_content)
            total_lines_match = re.search(r'总代码行数.*?(\d+,?\d*)行', readme_content)
            
            if file_count_match:
                declared_count = int(file_count_match.group(1))
                
                if actual_count == declared_count:
                    print(f"✅ Python文件数量一致: {actual_count}个")
                else:
                    print(f"❌ Python文件数量不一致: 实际={actual_count}, 声明={declared_count}")
                    return False
            
            # 统计实际代码行数
            total_lines = 0
            for py_file in py_files:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        total_lines += len(f.readlines())
                except:
                    pass
            
            if total_lines_match:
                declared_lines_str = total_lines_match.group(1).replace(',', '')
                declared_lines = int(declared_lines_str)
                
                if abs(total_lines - declared_lines) <= 100:  # 允许100行误差
                    print(f"✅ 代码行数基本一致: 实际={total_lines}, 声明={declared_lines}")
                else:
                    print(f"❌ 代码行数差异较大: 实际={total_lines}, 声明={declared_lines}")
                    return False
            else:
                print("⚠️ 未找到代码行数声明")
                return True
            
            return True
        
        print("❌ README.md 不存在")
        return False
    
    def check_module_structure(self):
        """检查模块结构一致性"""
        print("\n🔍 检查模块结构一致性...")
        
        # 统计各目录下的文件数量
        structure = {}
        for subdir in self.src_dir.iterdir():
            if subdir.is_dir() and not subdir.name.startswith('__'):
                py_files = list(subdir.glob("*.py"))
                structure[subdir.name] = len(py_files)
        
        # 检查README中的结构描述
        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
            
            # 查找模块描述
            inconsistencies = []
            for module_name, file_count in structure.items():
                pattern = rf'{module_name}/.*?#.*?\((\d+)个文件\)'
                match = re.search(pattern, readme_content)
                
                if match:
                    declared_count = int(match.group(1))
                    if file_count != declared_count:
                        inconsistencies.append(f"{module_name}: 实际={file_count}, 声明={declared_count}")
                else:
                    # 检查是否有其他形式的描述
                    if module_name in readme_content:
                        print(f"⚠️ {module_name} 模块存在但未找到文件数量声明")
            
            if not inconsistencies:
                print("✅ 模块结构描述一致")
                return True
            else:
                print("❌ 模块结构不一致:")
                for inconsistency in inconsistencies:
                    print(f"   {inconsistency}")
                return False
        
        print("❌ README.md 不存在")
        return False
    
    def check_test_coverage(self):
        """检查测试覆盖率描述"""
        print("\n🔍 检查测试覆盖率描述...")
        
        # 统计实际测试文件数量
        test_files = list(self.tests_dir.glob("test_*.py"))
        actual_test_count = len(test_files)
        
        # 检查README中的测试描述
        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
            
            # 查找测试数量声明
            test_count_match = re.search(r'(\d+)个测试文件', readme_content)
            
            if test_count_match:
                declared_test_count = int(test_count_match.group(1))
                
                if actual_test_count == declared_test_count:
                    print(f"✅ 测试文件数量一致: {actual_test_count}个")
                    return True
                else:
                    print(f"❌ 测试文件数量不一致: 实际={actual_test_count}, 声明={declared_test_count}")
                    return False
            else:
                print("⚠️ 未找到测试文件数量声明")
                return True
        
        print("❌ README.md 不存在")
        return False
    
    def check_docs_index(self):
        """检查文档索引完整性"""
        print("\n🔍 检查文档索引完整性...")
        
        docs_index_path = self.project_root / "DOCS_INDEX.md"
        if not docs_index_path.exists():
            print("❌ DOCS_INDEX.md 不存在")
            return False
        
        with open(docs_index_path, 'r', encoding='utf-8') as f:
            index_content = f.read()
        
        # 检查主要文档是否在索引中
        main_docs = [
            "README.md", "CHANGELOG.md", "DEPLOYMENT.md", 
            "TESTING.md", "FAQ.md", "CONTRIBUTING.md"
        ]
        
        missing_docs = []
        for doc in main_docs:
            if doc not in index_content:
                missing_docs.append(doc)
        
        if not missing_docs:
            print("✅ 主要文档都在索引中")
            return True
        else:
            print(f"❌ 索引中缺少文档: {', '.join(missing_docs)}")
            return False
    
    def generate_report(self):
        """生成完整的一致性检查报告"""
        print("=" * 60)
        print("  文档一致性检查报告")
        print("=" * 60)
        
        checks = [
            ("版本信息一致性", self.check_version_consistency),
            ("模块数量一致性", self.check_module_count),
            ("模块结构一致性", self.check_module_structure),
            ("测试覆盖率描述", self.check_test_coverage),
            ("文档索引完整性", self.check_docs_index),
        ]
        
        results = []
        for check_name, check_func in checks:
            try:
                result = check_func()
                results.append((check_name, result))
            except Exception as e:
                print(f"❌ {check_name} 检查失败: {e}")
                results.append((check_name, False))
        
        # 汇总结果
        print("\n" + "=" * 60)
        print("  检查结果汇总")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for check_name, result in results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{status}: {check_name}")
        
        print(f"\n✅ 通过: {passed}/{total}")
        print(f"❌ 失败: {total - passed}/{total}")
        
        if passed == total:
            print("\n🎉 所有检查通过！文档与代码保持一致。")
            return True
        else:
            print(f"\n⚠️ 发现 {total - passed} 个不一致问题，需要修复。")
            return False

def main():
    """主函数"""
    project_root = Path(__file__).parent.parent
    checker = DocumentConsistencyChecker(project_root)
    
    success = checker.generate_report()
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
