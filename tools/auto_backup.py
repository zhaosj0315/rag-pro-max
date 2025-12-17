#!/usr/bin/env python3
"""
自动备份工具 - 重构过程中的安全备份（仅代码相关）
"""

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

class AutoBackup:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root.parent / "refactor_backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # 只备份代码相关的目录和文件
        self.include_patterns = [
            "src/",
            "tests/", 
            "tools/",
            "scripts/",
            "config/",
            "docs/",
            "requirements.txt",
            "README.md",
            "*.py",
            "*.md",
            "*.json",
            "*.toml",
            "*.yml",
            "*.yaml",
            "Dockerfile",
            "docker-compose.yml",
            "*.spec",
            "LICENSE",
            ".gitignore",
            ".streamlit/",
            "kbllama"
        ]
        
        # 排除的目录（用户数据、缓存等）
        self.exclude_patterns = [
            "vector_db_storage/",
            "chat_histories/", 
            "temp_uploads/",
            "hf_cache/",
            "app_logs/",
            "suggestion_history/",
            "__pycache__/",
            "*.pyc",
            ".git/",
            "node_modules/",
            "dist/",
            "build/",
            ".cache/",
            "refactor_backups/"
        ]
        
    def should_include(self, path):
        """判断文件/目录是否应该备份"""
        path_str = str(path.relative_to(self.project_root))
        
        # 检查排除模式
        for pattern in self.exclude_patterns:
            if pattern.endswith('/'):
                if path_str.startswith(pattern) or f"/{pattern}" in path_str:
                    return False
            else:
                if path_str.endswith(pattern) or pattern in path_str:
                    return False
        
        # 检查包含模式
        for pattern in self.include_patterns:
            if pattern.endswith('/'):
                if path_str.startswith(pattern):
                    return True
            elif '*' in pattern:
                import fnmatch
                if fnmatch.fnmatch(path_str, pattern):
                    return True
            else:
                if path_str == pattern or path_str.endswith(f"/{pattern}"):
                    return True
        
        return False
        
    def create_snapshot(self, step_name):
        """创建重构步骤快照（仅代码相关）"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_name = f"{step_name}_{timestamp}"
        snapshot_path = self.backup_dir / snapshot_name
        
        print(f"📸 创建代码快照: {snapshot_name}")
        
        # 创建快照目录
        snapshot_path.mkdir(exist_ok=True)
        
        # 选择性复制文件
        copied_count = 0
        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)
            
            # 过滤目录
            dirs[:] = [d for d in dirs if self.should_include(root_path / d)]
            
            # 复制文件
            for file in files:
                file_path = root_path / file
                if self.should_include(file_path):
                    # 计算相对路径
                    rel_path = file_path.relative_to(self.project_root)
                    target_path = snapshot_path / rel_path
                    
                    # 创建目标目录
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 复制文件
                    shutil.copy2(file_path, target_path)
                    copied_count += 1
        
        # 创建Git提交
        self._create_git_commit(step_name)
        
        print(f"✅ 代码快照已保存: {snapshot_path}")
        print(f"📁 备份文件数: {copied_count}")
        return snapshot_path
        
    def _create_git_commit(self, step_name):
        """创建Git提交点"""
        try:
            os.chdir(self.project_root)
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', f'🔧 重构步骤: {step_name}'], check=True)
            print(f"✅ Git提交: {step_name}")
        except subprocess.CalledProcessError:
            print("⚠️ Git提交失败（可能没有变更）")
            
    def list_snapshots(self):
        """列出所有快照"""
        snapshots = list(self.backup_dir.glob("*"))
        snapshots.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        print("📋 可用代码快照:")
        for i, snapshot in enumerate(snapshots):
            mtime = datetime.fromtimestamp(snapshot.stat().st_mtime)
            print(f"  {i+1}. {snapshot.name} ({mtime.strftime('%Y-%m-%d %H:%M')})")
            
        return snapshots
        
    def restore_snapshot(self, snapshot_name):
        """恢复到指定快照"""
        snapshot_path = self.backup_dir / snapshot_name
        if not snapshot_path.exists():
            print(f"❌ 快照不存在: {snapshot_name}")
            return False
            
        print(f"🔄 恢复代码快照: {snapshot_name}")
        
        # 备份当前状态
        current_backup = self.backup_dir / f"before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.create_snapshot("before_restore")
        
        # 恢复文件（保留.git目录和用户数据）
        for item in snapshot_path.iterdir():
            if item.name in ['.git', 'vector_db_storage', 'chat_histories', 'temp_uploads', 'hf_cache', 'app_logs']:
                continue
                
            target = self.project_root / item.name
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
                    
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
                
        print(f"✅ 已恢复到: {snapshot_name}")
        print(f"📦 当前状态已备份")
        return True

def main():
    backup = AutoBackup()
    
    import sys
    if len(sys.argv) < 2:
        print("用法:")
        print("  python auto_backup.py snapshot <步骤名>  # 创建代码快照")
        print("  python auto_backup.py list              # 列出快照")
        print("  python auto_backup.py restore <快照名>   # 恢复快照")
        return
        
    command = sys.argv[1]
    
    if command == "snapshot":
        step_name = sys.argv[2] if len(sys.argv) > 2 else "manual"
        backup.create_snapshot(step_name)
    elif command == "list":
        backup.list_snapshots()
    elif command == "restore":
        snapshot_name = sys.argv[2] if len(sys.argv) > 2 else ""
        if not snapshot_name:
            snapshots = backup.list_snapshots()
            if snapshots:
                snapshot_name = snapshots[0].name
        backup.restore_snapshot(snapshot_name)

if __name__ == "__main__":
    main()
