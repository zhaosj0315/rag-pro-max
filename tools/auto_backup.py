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
        
    def create_snapshot(self, step_name):
        """创建重构步骤快照（仅代码相关）"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_name = f"{step_name}_{timestamp}"
        snapshot_path = self.backup_dir / snapshot_name
        
        print(f"📸 创建代码快照: {snapshot_name}")
        
        # 使用shutil.copytree的ignore参数来排除用户数据
        def ignore_user_data(dir, files):
            ignored = []
            for f in files:
                # 排除用户数据目录
                if f in ['vector_db_storage', 'chat_histories', 'temp_uploads', 'hf_cache', 'app_logs', 'suggestion_history']:
                    ignored.append(f)
                # 排除缓存文件
                elif f.endswith('.pyc') or f == '__pycache__':
                    ignored.append(f)
                # 排除之前的备份
                elif f == 'refactor_backups':
                    ignored.append(f)
            return ignored
        
        # 复制项目，排除用户数据
        shutil.copytree(self.project_root, snapshot_path, ignore=ignore_user_data)
        
        # 创建Git提交
        self._create_git_commit(step_name)
        
        # 统计备份文件数
        file_count = sum(1 for _ in snapshot_path.rglob('*') if _.is_file())
        
        print(f"✅ 代码快照已保存: {snapshot_path}")
        print(f"📁 备份文件数: {file_count}")
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
            file_count = sum(1 for _ in snapshot.rglob('*') if _.is_file())
            print(f"  {i+1}. {snapshot.name} ({mtime.strftime('%Y-%m-%d %H:%M')}) - {file_count}个文件")
            
        return snapshots
        
    def restore_snapshot(self, snapshot_name):
        """恢复到指定快照"""
        snapshot_path = self.backup_dir / snapshot_name
        if not snapshot_path.exists():
            print(f"❌ 快照不存在: {snapshot_name}")
            return False
            
        print(f"🔄 恢复代码快照: {snapshot_name}")
        
        # 备份当前状态
        self.create_snapshot("before_restore")
        
        # 恢复文件（保留用户数据目录）
        user_data_dirs = ['vector_db_storage', 'chat_histories', 'temp_uploads', 'hf_cache', 'app_logs', 'suggestion_history']
        
        for item in snapshot_path.iterdir():
            if item.name in ['.git'] + user_data_dirs:
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
        print(f"📦 用户数据已保留")
        return True

def main():
    backup = AutoBackup()
    
    import sys
    if len(sys.argv) < 2:
        print("用法:")
        print("  python auto_backup_fixed.py snapshot <步骤名>  # 创建代码快照")
        print("  python auto_backup_fixed.py list              # 列出快照")
        print("  python auto_backup_fixed.py restore <快照名>   # 恢复快照")
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
