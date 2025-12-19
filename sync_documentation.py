#!/usr/bin/env python3
"""
RAG Pro Max 文档逻辑同步工具
确保所有文档的版本、功能描述和架构信息保持一致
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging

class DocumentSyncManager:
    """文档同步管理器"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.setup_logging()
        self.version_pattern = r'v?(\d+\.\d+\.\d+)'
        
    def setup_logging(self):
        """设置日志"""
        log_dir = self.project_root / "sync_logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"doc_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def extract_version_from_readme(self) -> Optional[str]:
        """从README.md提取版本号"""
        readme_path = self.project_root / "README.md"
        if not readme_path.exists():
            return None
            
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 查找版本标识
        version_matches = re.findall(self.version_pattern, content)
        if version_matches:
            return version_matches[0]  # 返回第一个找到的版本号
        return None
    
    def extract_features_from_readme(self) -> List[str]:
        """从README.md提取核心功能列表"""
        readme_path = self.project_root / "README.md"
        if not readme_path.exists():
            return []
            
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        features = []
        
        # 提取核心功能部分
        feature_section = re.search(r'## ✨ 核心功能(.*?)(?=##|\Z)', content, re.DOTALL)
        if feature_section:
            feature_text = feature_section.group(1)
            
            # 提取功能标题
            feature_titles = re.findall(r'### 🎨 (.+)', feature_text)
            feature_titles.extend(re.findall(r'### 📄 (.+)', feature_text))
            feature_titles.extend(re.findall(r'### 🌐 (.+)', feature_text))
            feature_titles.extend(re.findall(r'### 🔍 (.+)', feature_text))
            feature_titles.extend(re.findall(r'### 💬 (.+)', feature_text))
            
            features.extend(feature_titles)
        
        return features
    
    def extract_architecture_from_readme(self) -> Dict[str, List[str]]:
        """从README.md提取架构信息"""
        readme_path = self.project_root / "README.md"
        if not readme_path.exists():
            return {}
            
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        architecture = {}
        
        # 提取四层架构设计
        arch_section = re.search(r'### 四层架构设计(.*?)### 核心模块', content, re.DOTALL)
        if arch_section:
            arch_text = arch_section.group(1)
            
            # 解析架构层
            layers = re.findall(r'(\w+层) \((\w+ \w+)\)\s*- (.+)', arch_text)
            for layer_cn, layer_en, description in layers:
                architecture[layer_cn] = {
                    "english": layer_en,
                    "description": description.strip()
                }
        
        return architecture
    
    def analyze_code_structure(self) -> Dict[str, Dict]:
        """分析实际代码结构"""
        src_path = self.project_root / "src"
        if not src_path.exists():
            return {}
        
        structure = {
            "directories": {},
            "core_files": {},
            "total_files": 0,
            "total_lines": 0
        }
        
        # 扫描目录结构
        for item in src_path.iterdir():
            if item.is_dir() and not item.name.startswith('__'):
                dir_info = self._analyze_directory(item)
                structure["directories"][item.name] = dir_info
                structure["total_files"] += dir_info["file_count"]
                structure["total_lines"] += dir_info["total_lines"]
        
        # 分析核心文件
        core_files = ["apppro.py", "file_processor.py", "rag_engine.py"]
        for core_file in core_files:
            file_path = src_path / core_file
            if file_path.exists():
                structure["core_files"][core_file] = self._analyze_file(file_path)
                structure["total_lines"] += structure["core_files"][core_file]["lines"]
        
        return structure
    
    def _analyze_directory(self, directory: Path) -> Dict:
        """分析目录"""
        info = {
            "file_count": 0,
            "total_lines": 0,
            "file_types": {},
            "files": []
        }
        
        for file_path in directory.rglob("*.py"):
            if not any(part.startswith('__') for part in file_path.parts):
                file_info = self._analyze_file(file_path)
                info["files"].append({
                    "name": file_path.name,
                    "path": str(file_path.relative_to(self.project_root)),
                    "lines": file_info["lines"]
                })
                info["file_count"] += 1
                info["total_lines"] += file_info["lines"]
                
                ext = file_path.suffix
                info["file_types"][ext] = info["file_types"].get(ext, 0) + 1
        
        return info
    
    def _analyze_file(self, file_path: Path) -> Dict:
        """分析单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            return {
                "lines": len(lines),
                "size": file_path.stat().st_size,
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }
        except Exception as e:
            self.logger.warning(f"无法分析文件 {file_path}: {e}")
            return {"lines": 0, "size": 0, "modified": ""}
    
    def check_version_consistency(self) -> Dict[str, str]:
        """检查版本一致性"""
        versions = {}
        
        # 检查README.md
        readme_version = self.extract_version_from_readme()
        if readme_version:
            versions["README.md"] = readme_version
        
        # 检查其他可能包含版本的文件
        version_files = [
            "CHANGELOG.md",
            "src/apppro.py",
            "requirements.txt"
        ]
        
        for file_name in version_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                version = self._extract_version_from_file(file_path)
                if version:
                    versions[file_name] = version
        
        return versions
    
    def _extract_version_from_file(self, file_path: Path) -> Optional[str]:
        """从文件中提取版本号"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            version_matches = re.findall(self.version_pattern, content)
            if version_matches:
                return version_matches[0]
        except Exception as e:
            self.logger.warning(f"无法读取文件 {file_path}: {e}")
        
        return None
    
    def generate_architecture_summary(self) -> str:
        """生成架构总结"""
        code_structure = self.analyze_code_structure()
        readme_architecture = self.extract_architecture_from_readme()
        
        summary = f"""
# RAG Pro Max 架构分析报告
生成时间: {datetime.now().isoformat()}

## 代码结构统计
- 总文件数: {code_structure['total_files']}
- 总代码行数: {code_structure['total_lines']:,}
- 目录数量: {len(code_structure['directories'])}
- 核心文件数: {len(code_structure['core_files'])}

## 目录结构分析
"""
        
        for dir_name, dir_info in code_structure["directories"].items():
            summary += f"\n### {dir_name}/\n"
            summary += f"- 文件数: {dir_info['file_count']}\n"
            summary += f"- 代码行数: {dir_info['total_lines']:,}\n"
            summary += f"- 主要文件:\n"
            
            # 显示前5个最大的文件
            sorted_files = sorted(dir_info['files'], key=lambda x: x['lines'], reverse=True)[:5]
            for file_info in sorted_files:
                summary += f"  - {file_info['name']}: {file_info['lines']} 行\n"
        
        summary += "\n## 核心文件分析\n"
        for file_name, file_info in code_structure["core_files"].items():
            summary += f"- {file_name}: {file_info['lines']:,} 行, {file_info['size']:,} bytes\n"
        
        return summary
    
    def sync_documentation(self) -> Dict:
        """同步文档逻辑"""
        self.logger.info("开始同步文档逻辑...")
        
        # 1. 检查版本一致性
        versions = self.check_version_consistency()
        
        # 2. 提取README信息
        current_version = self.extract_version_from_readme()
        features = self.extract_features_from_readme()
        architecture = self.extract_architecture_from_readme()
        
        # 3. 分析代码结构
        code_structure = self.analyze_code_structure()
        
        # 4. 生成架构总结
        arch_summary = self.generate_architecture_summary()
        
        # 5. 创建同步报告
        sync_report = {
            "timestamp": datetime.now().isoformat(),
            "current_version": current_version,
            "version_consistency": versions,
            "features_count": len(features),
            "architecture_layers": len(architecture),
            "code_statistics": {
                "total_files": code_structure["total_files"],
                "total_lines": code_structure["total_lines"],
                "directories": len(code_structure["directories"]),
                "core_files": len(code_structure["core_files"])
            },
            "features": features,
            "architecture": architecture
        }
        
        # 6. 保存结果
        sync_dir = self.project_root / "sync_results"
        sync_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存详细报告
        with open(sync_dir / f"doc_sync_report_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(sync_report, f, indent=2, ensure_ascii=False)
        
        # 保存架构总结
        with open(sync_dir / f"architecture_summary_{timestamp}.md", 'w', encoding='utf-8') as f:
            f.write(arch_summary)
        
        self.logger.info("文档同步完成!")
        return sync_report
    
    def validate_documentation(self) -> List[str]:
        """验证文档完整性"""
        issues = []
        
        # 检查必需文档
        required_docs = [
            "README.md",
            "DEPLOYMENT.md", 
            "CHANGELOG.md",
            "API_DOCUMENTATION.md"
        ]
        
        for doc in required_docs:
            doc_path = self.project_root / doc
            if not doc_path.exists():
                issues.append(f"缺失文档: {doc}")
            elif doc_path.stat().st_size == 0:
                issues.append(f"空文档: {doc}")
        
        # 检查版本一致性
        versions = self.check_version_consistency()
        if len(set(versions.values())) > 1:
            issues.append(f"版本不一致: {versions}")
        
        # 检查README结构
        readme_path = self.project_root / "README.md"
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_sections = [
                "核心功能",
                "系统架构", 
                "快速开始",
                "技术栈"
            ]
            
            for section in required_sections:
                if section not in content:
                    issues.append(f"README缺失章节: {section}")
        
        return issues

def main():
    """主函数"""
    print("📚 RAG Pro Max 文档逻辑同步工具")
    print("=" * 50)
    
    # 初始化文档同步管理器
    doc_sync = DocumentSyncManager()
    
    try:
        # 验证文档
        issues = doc_sync.validate_documentation()
        if issues:
            print(f"\n⚠️  发现 {len(issues)} 个文档问题:")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print("\n✅ 文档验证通过!")
        
        # 执行同步
        result = doc_sync.sync_documentation()
        
        print(f"\n📊 同步结果:")
        print(f"  - 当前版本: {result['current_version']}")
        print(f"  - 核心功能: {result['features_count']} 个")
        print(f"  - 架构层数: {result['architecture_layers']} 层")
        print(f"  - 代码文件: {result['code_statistics']['total_files']} 个")
        print(f"  - 代码行数: {result['code_statistics']['total_lines']:,} 行")
        
        print(f"\n📋 核心功能列表:")
        for i, feature in enumerate(result['features'][:5], 1):
            print(f"  {i}. {feature}")
        
        print(f"\n🏗️  架构层级:")
        for layer, info in result['architecture'].items():
            print(f"  - {layer}: {info['description']}")
        
        print(f"\n💾 报告已保存至 sync_results/ 目录")
        
    except Exception as e:
        print(f"❌ 文档同步失败: {e}")
        logging.error(f"文档同步失败: {e}", exc_info=True)

if __name__ == "__main__":
    main()
