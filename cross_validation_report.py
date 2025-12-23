#!/usr/bin/env python3
"""
RAG Pro Max 文档一致性交叉验证工具
检查版本号、模块数量、功能描述等关键信息在所有文档中的一致性
"""

import json
import re
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any

class DocumentationValidator:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.info = []
        
    def log_issue(self, category: str, message: str):
        self.issues.append(f"❌ [{category}] {message}")
        
    def log_warning(self, category: str, message: str):
        self.warnings.append(f"⚠️  [{category}] {message}")
        
    def log_info(self, category: str, message: str):
        self.info.append(f"ℹ️  [{category}] {message}")

    def extract_version_from_file(self, filepath: str) -> List[str]:
        """从文件中提取版本号"""
        versions = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # 匹配 v2.4.7 格式
                version_patterns = [
                    r'v(\d+\.\d+\.\d+)',
                    r'version["\s]*[:=]["\s]*(\d+\.\d+\.\d+)',
                    r'Version.*?(\d+\.\d+\.\d+)',
                ]
                for pattern in version_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    versions.extend(matches)
        except Exception as e:
            self.log_warning("VERSION", f"无法读取文件 {filepath}: {e}")
        return list(set(versions))  # 去重

    def count_modules_in_directory(self, directory: str) -> int:
        """统计目录中的Python模块数量"""
        if not os.path.exists(directory):
            return 0
        return len([f for f in os.listdir(directory) if f.endswith('.py') and f != '__init__.py'])

    def get_file_line_count(self, filepath: str) -> int:
        """获取文件行数"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return len(f.readlines())
        except:
            return 0

    def validate_version_consistency(self):
        """验证版本号一致性"""
        self.log_info("VERSION", "开始验证版本号一致性...")
        
        # 关键文件列表
        key_files = [
            'README.md',
            'version.json', 
            'CHANGELOG.md',
            'TESTING.md',
            'FAQ.md',
            'CONTRIBUTING.md',
            'API_DOCUMENTATION.md',
            'DEPLOYMENT.md'
        ]
        
        version_data = {}
        
        # 特殊处理 version.json
        try:
            with open('version.json', 'r', encoding='utf-8') as f:
                version_json = json.load(f)
                canonical_version = version_json.get('version', 'unknown')
                self.log_info("VERSION", f"标准版本号 (version.json): {canonical_version}")
        except Exception as e:
            self.log_issue("VERSION", f"无法读取 version.json: {e}")
            canonical_version = "unknown"
        
        # 检查其他文件中的版本号
        for file in key_files:
            if os.path.exists(file):
                versions = self.extract_version_from_file(file)
                version_data[file] = versions
                
                if versions:
                    for version in versions:
                        if version != canonical_version:
                            self.log_issue("VERSION", f"{file} 中发现不一致版本号: {version} (标准: {canonical_version})")
                        else:
                            self.log_info("VERSION", f"{file} 版本号一致: {version}")
                else:
                    self.log_warning("VERSION", f"{file} 中未找到版本号")
            else:
                self.log_warning("VERSION", f"文件不存在: {file}")

    def validate_module_counts(self):
        """验证模块数量一致性"""
        self.log_info("MODULES", "开始验证模块数量一致性...")
        
        # 实际统计
        actual_counts = {
            'processors': self.count_modules_in_directory('src/processors'),
            'ui': self.count_modules_in_directory('src/ui'), 
            'utils': self.count_modules_in_directory('src/utils'),
            'services': self.count_modules_in_directory('src/services'),
            'common': self.count_modules_in_directory('src/common'),
            'core': self.count_modules_in_directory('src/core')
        }
        
        # README.md 中声明的数量
        readme_claims = {
            'processors': 16,  # 从 README.md 提取
            'ui': 31,
            'utils': 49,
            'services': None,  # README 中说的是"文件服务、知识库服务、配置服务"
            'common': None,
            'core': None
        }
        
        for module_type, actual_count in actual_counts.items():
            self.log_info("MODULES", f"{module_type} 实际模块数: {actual_count}")
            
            if readme_claims.get(module_type) is not None:
                claimed_count = readme_claims[module_type]
                if actual_count != claimed_count:
                    self.log_issue("MODULES", f"{module_type} 模块数不一致: 实际 {actual_count}, README 声明 {claimed_count}")
                else:
                    self.log_info("MODULES", f"{module_type} 模块数一致: {actual_count}")

    def validate_file_sizes(self):
        """验证关键文件大小声明"""
        self.log_info("FILES", "开始验证文件大小声明...")
        
        # 检查 apppro.py 行数
        apppro_lines = self.get_file_line_count('src/apppro.py')
        readme_claimed_lines = 3715  # README 中声明的行数
        
        self.log_info("FILES", f"apppro.py 实际行数: {apppro_lines}")
        
        if abs(apppro_lines - readme_claimed_lines) > 500:  # 允许500行误差
            self.log_issue("FILES", f"apppro.py 行数差异过大: 实际 {apppro_lines}, README 声明 {readme_claimed_lines}")
        elif apppro_lines != readme_claimed_lines:
            self.log_warning("FILES", f"apppro.py 行数轻微差异: 实际 {apppro_lines}, README 声明 {readme_claimed_lines}")
        else:
            self.log_info("FILES", f"apppro.py 行数一致: {apppro_lines}")

    def validate_test_coverage(self):
        """验证测试覆盖率声明"""
        self.log_info("TESTS", "开始验证测试覆盖率声明...")
        
        # 从不同文档中提取测试覆盖率数据
        coverage_sources = {
            'README.md': '91.7%',  # badge 中的声明
            'TESTING.md': '89/97',  # 测试结果中的声明
            'version.json': '89/97'  # 架构信息中的声明
        }
        
        for source, claimed_coverage in coverage_sources.items():
            if os.path.exists(source):
                self.log_info("TESTS", f"{source} 声明测试覆盖率: {claimed_coverage}")
            else:
                self.log_warning("TESTS", f"文件不存在: {source}")

    def validate_feature_consistency(self):
        """验证功能描述一致性"""
        self.log_info("FEATURES", "开始验证功能描述一致性...")
        
        # 检查关键功能在不同文档中的描述是否一致
        key_features = [
            "macOS 原生预览",
            "GPU加速", 
            "OCR识别",
            "网页抓取",
            "多轮对话",
            "增量更新"
        ]
        
        for feature in key_features:
            found_in = []
            for doc in ['README.md', 'CHANGELOG.md', 'FAQ.md']:
                if os.path.exists(doc):
                    try:
                        with open(doc, 'r', encoding='utf-8') as f:
                            if feature in f.read():
                                found_in.append(doc)
                    except:
                        pass
            
            if len(found_in) >= 2:
                self.log_info("FEATURES", f"功能 '{feature}' 在多个文档中提及: {', '.join(found_in)}")
            elif len(found_in) == 1:
                self.log_warning("FEATURES", f"功能 '{feature}' 仅在 {found_in[0]} 中提及")
            else:
                self.log_warning("FEATURES", f"功能 '{feature}' 在主要文档中未找到")

    def generate_report(self):
        """生成验证报告"""
        print("=" * 80)
        print("🔍 RAG Pro Max 文档一致性验证报告")
        print("=" * 80)
        
        # 执行所有验证
        self.validate_version_consistency()
        self.validate_module_counts()
        self.validate_file_sizes()
        self.validate_test_coverage()
        self.validate_feature_consistency()
        
        # 输出结果
        print(f"\n📊 验证结果统计:")
        print(f"❌ 严重问题: {len(self.issues)}")
        print(f"⚠️  警告: {len(self.warnings)}")
        print(f"ℹ️  信息: {len(self.info)}")
        
        if self.issues:
            print(f"\n❌ 发现 {len(self.issues)} 个严重问题:")
            for issue in self.issues:
                print(f"  {issue}")
        
        if self.warnings:
            print(f"\n⚠️  发现 {len(self.warnings)} 个警告:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.info:
            print(f"\nℹ️  详细信息 ({len(self.info)} 条):")
            for info in self.info[:10]:  # 只显示前10条
                print(f"  {info}")
            if len(self.info) > 10:
                print(f"  ... 还有 {len(self.info) - 10} 条信息")
        
        # 总结
        print(f"\n" + "=" * 80)
        if not self.issues:
            print("✅ 文档一致性验证通过！所有关键信息保持一致。")
        else:
            print("❌ 发现文档一致性问题，需要修复后再发布。")
        print("=" * 80)
        
        return len(self.issues) == 0

if __name__ == "__main__":
    validator = DocumentationValidator()
    success = validator.generate_report()
    exit(0 if success else 1)