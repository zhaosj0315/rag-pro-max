#!/usr/bin/env python3
"""
自动备份工具 - 重构过程中的安全备份
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
        
    def create_snapshot(self, step_name):
        """创建重构步骤快照"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_name = f"{step_name}_{timestamp}"
        snapshot_path = self.backup_dir / snapshot_name
        
        print(f"📸 创建快照: {snapshot_name}")
        
        # 复制整个项目
        shutil.copytree(self.project_root, snapshot_path, 
                       ignore=shutil.ignore_patterns('*.pyc', '__pycache__', '.git'))
        
        # 创建Git提交
        self._create_git_commit(step_name)
        
        print(f"✅ 快照已保存: {snapshot_path}")
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
        
        print("📋 可用快照:")
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
            
        print(f"🔄 恢复快照: {snapshot_name}")
        
        # 备份当前状态
        current_backup = self.backup_dir / f"before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copytree(self.project_root, current_backup,
                       ignore=shutil.ignore_patterns('*.pyc', '__pycache__', '.git'))
        
        # 恢复文件（保留.git目录）
        for item in snapshot_path.iterdir():
            if item.name == '.git':
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
        print(f"📦 当前状态已备份到: {current_backup.name}")
        return True

def main():
    backup = AutoBackup()
    
    import sys
    if len(sys.argv) < 2:
        print("用法:")
        print("  python auto_backup.py snapshot <步骤名>  # 创建快照")
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
