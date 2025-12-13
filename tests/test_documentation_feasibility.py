#!/usr/bin/env python3
"""
文档更新可行性测试
验证所有文档的完整性和一致性
"""

import os
import sys
import unittest
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestDocumentationFeasibility(unittest.TestCase):
    """文档更新可行性测试"""
    
    def setUp(self):
        """测试前准备"""
        self.project_root = Path(__file__).parent.parent
        self.docs_dir = self.project_root / "docs"
        self.src_dir = self.project_root / "src"
    
    def test_core_documentation_exists(self):
        """测试核心文档是否存在"""
        required_docs = [
            "README.md",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "LICENSE"
        ]
        
        for doc in required_docs:
            doc_path = self.project_root / doc
            self.assertTrue(doc_path.exists(), f"缺少核心文档: {doc}")
            
            # 检查文档是否为空
            if doc_path.suffix == ".md":
                content = doc_path.read_text(encoding='utf-8')
                self.assertGreater(len(content), 100, f"文档内容过少: {doc}")
        
        print("✅ 核心文档完整性检查通过")
    
    def test_stage_documentation_exists(self):
        """测试阶段文档是否存在"""
        stage_docs = [
            "core/STAGE14_REFACTOR_SUMMARY.md",
            "core/STAGE15_REFACTOR_SUMMARY.md", 
            "core/STAGE16_REFACTOR_SUMMARY.md",
            "core/STAGE17_FINAL_OPTIMIZATION.md",
            "core/MAIN_FILE_SIMPLIFICATION.md"
        ]
        
        for doc in stage_docs:
            doc_path = self.docs_dir / doc
            self.assertTrue(doc_path.exists(), f"缺少阶段文档: {doc}")
            
            content = doc_path.read_text(encoding='utf-8')
            self.assertGreater(len(content), 500, f"阶段文档内容过少: {doc}")
        
        print("✅ 阶段文档完整性检查通过")
    
    def test_technical_documentation_exists(self):
        """测试技术文档是否存在"""
        tech_docs = [
            "PROJECT_STATUS_STAGE14.md",
            "QUEUE_BLOCKING_FIX.md",
            "STAGE14_HOTFIX.md",
            "CODE_QUALITY_REPORT.md"
        ]
        
        existing_count = 0
        for doc in tech_docs:
            doc_path = self.docs_dir / doc
            if doc_path.exists():
                existing_count += 1
        
        # 至少要有 75% 的技术文档存在
        coverage = existing_count / len(tech_docs)
        self.assertGreaterEqual(coverage, 0.75, f"技术文档覆盖率过低: {coverage:.1%}")
        
        print(f"✅ 技术文档覆盖率: {coverage:.1%}")
    
    def test_module_documentation_consistency(self):
        """测试模块文档一致性"""
        # 检查每个模块是否有文档字符串
        py_files = list(self.src_dir.rglob("*.py"))
        py_files = [f for f in py_files if not f.name.startswith("__")]
        
        documented_files = 0
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                if '"""' in content or "'''" in content:
                    documented_files += 1
            except:
                pass
        
        documentation_rate = documented_files / len(py_files) if py_files else 0
        self.assertGreaterEqual(documentation_rate, 0.8, f"模块文档覆盖率过低: {documentation_rate:.1%}")
        
        print(f"✅ 模块文档覆盖率: {documentation_rate:.1%}")
    
    def test_readme_accuracy(self):
        """测试 README 准确性"""
        readme_path = self.project_root / "README.md"
        self.assertTrue(readme_path.exists(), "README.md 不存在")
        
        content = readme_path.read_text(encoding='utf-8')
        
        # 检查版本信息
        self.assertIn("v2.3.0", content, "版本信息需要更新")
        
        # 检查功能特性
        required_features = [
            "多格式支持",
            "OCR识别", 
            "语义检索",
            "Re-ranking",
            "BM25",
            "多轮对话"
        ]
        
        for feature in required_features:
            self.assertIn(feature, content, f"README 缺少功能描述: {feature}")
        
        print("✅ README 准确性检查通过")
    
    def test_changelog_completeness(self):
        """测试更新日志完整性"""
        changelog_path = self.project_root / "CHANGELOG.md"
        
        if changelog_path.exists():
            content = changelog_path.read_text(encoding='utf-8')
            
            # 检查最新版本
            self.assertIn("v2.3.0", content, "CHANGELOG 需要更新最新版本")
            
            # 检查重构记录
            stage_keywords = ["Stage 14", "Stage 15", "Stage 16", "重构"]
            has_refactor_info = any(keyword in content for keyword in stage_keywords)
            self.assertTrue(has_refactor_info, "CHANGELOG 缺少重构信息")
            
            print("✅ CHANGELOG 完整性检查通过")
        else:
            print("⚠️ CHANGELOG.md 不存在，需要创建")
    
    def test_api_documentation_feasibility(self):
        """测试 API 文档可行性"""
        # 检查是否有足够的模块可以生成 API 文档
        py_files = list(self.src_dir.rglob("*.py"))
        classes_and_functions = 0
        
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                classes_and_functions += content.count("class ")
                classes_and_functions += content.count("def ")
            except:
                pass
        
        # 至少要有 100 个类和函数才值得生成 API 文档
        self.assertGreaterEqual(classes_and_functions, 100, 
                               f"API 文档生成可行性不足: 仅 {classes_and_functions} 个类/函数")
        
        print(f"✅ API 文档可行性: {classes_and_functions} 个类/函数")
    
    def test_deployment_guide_feasibility(self):
        """测试部署指南可行性"""
        # 检查部署相关文件
        deployment_files = [
            "Dockerfile",
            "docker-compose.yml",
            "requirements.txt",
            "scripts/deploy_linux.sh",
            "scripts/deploy_windows.bat"
        ]
        
        existing_files = 0
        for file_path in deployment_files:
            if (self.project_root / file_path).exists():
                existing_files += 1
        
        coverage = existing_files / len(deployment_files)
        self.assertGreaterEqual(coverage, 0.8, f"部署文件覆盖率过低: {coverage:.1%}")
        
        print(f"✅ 部署指南可行性: {coverage:.1%} 文件覆盖")

def run_tests():
    """运行测试"""
    print("=" * 60)
    print("  文档更新可行性测试")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDocumentationFeasibility)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
    print("\n" + "=" * 60)
    print("  测试结果汇总")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"✅ 通过: {passed}/{total_tests}")
    print(f"❌ 失败: {failures}/{total_tests}")
    print(f"💥 错误: {errors}/{total_tests}")
    
    if failures == 0 and errors == 0:
        print("\n🎉 文档更新可行性验证通过！")
        return True
    else:
        print(f"\n⚠️ 发现 {failures + errors} 个问题，需要修复。")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
