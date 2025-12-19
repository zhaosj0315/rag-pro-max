#!/usr/bin/env python3
"""
RAG Pro Max 代码同步工具
基于四层架构设计的完整代码和文档逻辑同步
"""

import os
import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple
import logging

class CodeSyncManager:
    """代码同步管理器"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.sync_config = self._load_sync_config()
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        log_dir = self.project_root / "sync_logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _load_sync_config(self) -> Dict:
        """加载同步配置"""
        config_file = self.project_root / "sync_config.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 默认配置
        default_config = {
            "architecture_layers": {
                "ui": ["src/ui/", "src/app/", "src/auth/"],
                "service": ["src/services/", "src/processors/", "src/engines/"],
                "common": ["src/common/", "src/utils/", "src/config/"],
                "tools": ["src/api/", "src/monitoring/", "src/queue/"]
            },
            "core_files": [
                "src/apppro.py",
                "src/file_processor.py", 
                "src/rag_engine.py"
            ],
            "documentation": [
                "README.md",
                "DEPLOYMENT.md",
                "API_DOCUMENTATION.md",
                "CHANGELOG.md"
            ],
            "exclude_patterns": [
                "__pycache__",
                "*.pyc",
                ".git",
                "node_modules",
                "temp_uploads",
                "vector_db_storage",
                "chat_histories",
                "app_logs"
            ]
        }
        
        # 保存默认配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
            
        return default_config
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            self.logger.warning(f"无法计算文件哈希: {file_path} - {e}")
            return ""
    
    def scan_codebase(self) -> Dict[str, Dict]:
        """扫描代码库"""
        codebase_info = {
            "timestamp": datetime.now().isoformat(),
            "layers": {},
            "core_files": {},
            "documentation": {},
            "statistics": {}
        }
        
        # 扫描架构层
        for layer_name, directories in self.sync_config["architecture_layers"].items():
            layer_files = {}
            for directory in directories:
                dir_path = self.project_root / directory
                if dir_path.exists():
                    layer_files.update(self._scan_directory(dir_path))
            codebase_info["layers"][layer_name] = layer_files
        
        # 扫描核心文件
        for core_file in self.sync_config["core_files"]:
            file_path = self.project_root / core_file
            if file_path.exists():
                codebase_info["core_files"][core_file] = {
                    "hash": self.calculate_file_hash(file_path),
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
        
        # 扫描文档
        for doc_file in self.sync_config["documentation"]:
            file_path = self.project_root / doc_file
            if file_path.exists():
                codebase_info["documentation"][doc_file] = {
                    "hash": self.calculate_file_hash(file_path),
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
        
        # 统计信息
        total_files = sum(len(files) for files in codebase_info["layers"].values())
        total_files += len(codebase_info["core_files"])
        total_files += len(codebase_info["documentation"])
        
        codebase_info["statistics"] = {
            "total_files": total_files,
            "layers_count": len(codebase_info["layers"]),
            "core_files_count": len(codebase_info["core_files"]),
            "documentation_count": len(codebase_info["documentation"])
        }
        
        return codebase_info
    
    def _scan_directory(self, directory: Path) -> Dict[str, Dict]:
        """扫描目录"""
        files_info = {}
        
        for file_path in directory.rglob("*"):
            if file_path.is_file() and not self._should_exclude(file_path):
                relative_path = str(file_path.relative_to(self.project_root))
                files_info[relative_path] = {
                    "hash": self.calculate_file_hash(file_path),
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    "extension": file_path.suffix
                }
        
        return files_info
    
    def _should_exclude(self, file_path: Path) -> bool:
        """检查是否应该排除文件"""
        path_str = str(file_path)
        for pattern in self.sync_config["exclude_patterns"]:
            if pattern in path_str:
                return True
        return False
    
    def generate_sync_report(self) -> str:
        """生成同步报告"""
        codebase_info = self.scan_codebase()
        
        report = f"""
# RAG Pro Max 代码同步报告
生成时间: {codebase_info['timestamp']}

## 项目概览
- 总文件数: {codebase_info['statistics']['total_files']}
- 架构层数: {codebase_info['statistics']['layers_count']}
- 核心文件数: {codebase_info['statistics']['core_files_count']}
- 文档文件数: {codebase_info['statistics']['documentation_count']}

## 四层架构分析

### 表现层 (UI Layer)
"""
        
        # 分析各层
        for layer_name, files in codebase_info["layers"].items():
            layer_display = {
                "ui": "表现层 (UI Layer)",
                "service": "服务层 (Service Layer)", 
                "common": "公共层 (Common Layer)",
                "tools": "工具层 (Tools Layer)"
            }
            
            report += f"\n### {layer_display.get(layer_name, layer_name)}\n"
            report += f"文件数量: {len(files)}\n"
            
            # 按文件类型统计
            extensions = {}
            for file_info in files.values():
                ext = file_info.get('extension', 'unknown')
                extensions[ext] = extensions.get(ext, 0) + 1
            
            report += "文件类型分布:\n"
            for ext, count in sorted(extensions.items()):
                report += f"  - {ext or '无扩展名'}: {count} 个文件\n"
        
        # 核心文件状态
        report += "\n## 核心文件状态\n"
        for file_name, file_info in codebase_info["core_files"].items():
            report += f"- {file_name}: {file_info['size']} bytes, 修改时间: {file_info['modified']}\n"
        
        # 文档状态
        report += "\n## 文档状态\n"
        for doc_name, doc_info in codebase_info["documentation"].items():
            report += f"- {doc_name}: {doc_info['size']} bytes, 修改时间: {doc_info['modified']}\n"
        
        return report
    
    def create_backup(self) -> str:
        """创建备份"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.project_root / "backups" / f"backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"创建备份到: {backup_dir}")
        
        # 备份核心文件和目录
        backup_items = [
            "src/",
            "config/",
            "README.md",
            "requirements.txt"
        ]
        
        for item in backup_items:
            source = self.project_root / item
            if source.exists():
                if source.is_dir():
                    shutil.copytree(source, backup_dir / item, ignore=shutil.ignore_patterns(*self.sync_config["exclude_patterns"]))
                else:
                    shutil.copy2(source, backup_dir / item)
        
        # 保存同步信息
        sync_info = self.scan_codebase()
        with open(backup_dir / "sync_info.json", 'w', encoding='utf-8') as f:
            json.dump(sync_info, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"备份完成: {backup_dir}")
        return str(backup_dir)
    
    def validate_architecture(self) -> List[str]:
        """验证架构完整性"""
        issues = []
        
        # 检查核心文件
        for core_file in self.sync_config["core_files"]:
            file_path = self.project_root / core_file
            if not file_path.exists():
                issues.append(f"缺失核心文件: {core_file}")
        
        # 检查架构层目录
        for layer_name, directories in self.sync_config["architecture_layers"].items():
            for directory in directories:
                dir_path = self.project_root / directory
                if not dir_path.exists():
                    issues.append(f"缺失{layer_name}层目录: {directory}")
        
        # 检查文档
        for doc_file in self.sync_config["documentation"]:
            file_path = self.project_root / doc_file
            if not file_path.exists():
                issues.append(f"缺失文档文件: {doc_file}")
        
        return issues
    
    def sync_all(self) -> Dict:
        """执行完整同步"""
        self.logger.info("开始执行完整代码同步...")
        
        # 1. 验证架构
        issues = self.validate_architecture()
        if issues:
            self.logger.warning(f"发现架构问题: {len(issues)} 个")
            for issue in issues:
                self.logger.warning(f"  - {issue}")
        
        # 2. 创建备份
        backup_path = self.create_backup()
        
        # 3. 扫描代码库
        codebase_info = self.scan_codebase()
        
        # 4. 生成报告
        report = self.generate_sync_report()
        
        # 5. 保存同步结果
        sync_result_dir = self.project_root / "sync_results"
        sync_result_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存详细信息
        with open(sync_result_dir / f"codebase_info_{timestamp}.json", 'w', encoding='utf-8') as f:
            json.dump(codebase_info, f, indent=2, ensure_ascii=False)
        
        # 保存报告
        with open(sync_result_dir / f"sync_report_{timestamp}.md", 'w', encoding='utf-8') as f:
            f.write(report)
        
        sync_summary = {
            "timestamp": datetime.now().isoformat(),
            "backup_path": backup_path,
            "total_files": codebase_info["statistics"]["total_files"],
            "architecture_issues": len(issues),
            "sync_status": "completed"
        }
        
        self.logger.info(f"同步完成! 总文件数: {sync_summary['total_files']}")
        self.logger.info(f"备份路径: {backup_path}")
        self.logger.info(f"报告保存至: sync_results/")
        
        return sync_summary

def main():
    """主函数"""
    print("🚀 RAG Pro Max 代码同步工具")
    print("=" * 50)
    
    # 初始化同步管理器
    sync_manager = CodeSyncManager()
    
    try:
        # 执行同步
        result = sync_manager.sync_all()
        
        print("\n✅ 同步完成!")
        print(f"📊 总文件数: {result['total_files']}")
        print(f"💾 备份路径: {result['backup_path']}")
        print(f"⚠️  架构问题: {result['architecture_issues']} 个")
        
        # 显示报告预览
        print("\n📋 同步报告预览:")
        print("-" * 30)
        report = sync_manager.generate_sync_report()
        print(report[:500] + "..." if len(report) > 500 else report)
        
    except Exception as e:
        print(f"❌ 同步失败: {e}")
        logging.error(f"同步失败: {e}", exc_info=True)

if __name__ == "__main__":
    main()
