#!/usr/bin/env python3
"""
RAG Pro Max 任务启动器
自动化单功能迭代开发流程 - 支持V2.0规范
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

class TaskStarter:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.iteration_log = self.project_root / "iteration_log.json"
        
    def start_new_task(self, feature_name: str, description: str):
        """启动新任务 - 完整的V2.0流程"""
        
        print("🚀 启动单功能迭代开发流程 V2.0")
        print("=" * 50)
        
        # 1️⃣ 分析与快照
        if not self._analyze_and_snapshot():
            return False
        
        # 2️⃣ 选择与建枝
        branch_name = self._select_and_branch(feature_name)
        if not branch_name:
            return False
        
        # 3️⃣ 记录任务
        task_id = self._record_task(feature_name, description, branch_name)
        
        print(f"\n✅ 任务启动成功！")
        print(f"📋 任务ID: {task_id}")
        print(f"🌿 分支名称: {branch_name}")
        print(f"📝 下一步: 开始实现功能代码")
        
        return True
    
    def _analyze_and_snapshot(self) -> bool:
        """1️⃣ 分析与快照阶段"""
        print("\n1️⃣ 分析与快照阶段")
        
        # Git检查：确保主分支干净
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.stdout.strip():
                print("❌ Git状态不干净，请先提交或暂存当前更改")
                print("未提交的文件:")
                print(result.stdout)
                return False
            else:
                print("✅ Git状态干净")
        except Exception as e:
            print(f"❌ Git检查失败: {e}")
            return False
        
        # 依赖锁定检查
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            print("✅ requirements.txt存在")
        else:
            print("⚠️ requirements.txt不存在，建议创建")
        
        # 确保在主分支
        try:
            result = subprocess.run(['git', 'branch', '--show-current'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            current_branch = result.stdout.strip()
            
            if current_branch not in ['main', 'master']:
                print(f"⚠️ 当前不在主分支 (当前: {current_branch})")
                switch = input("是否切换到main分支? (y/n): ")
                if switch.lower() == 'y':
                    subprocess.run(['git', 'checkout', 'main'], cwd=self.project_root)
                    print("✅ 已切换到main分支")
                else:
                    return False
            else:
                print(f"✅ 当前在主分支: {current_branch}")
        except Exception as e:
            print(f"❌ 分支检查失败: {e}")
            return False
        
        # 拉取最新代码
        try:
            subprocess.run(['git', 'pull'], cwd=self.project_root, check=True)
            print("✅ 已拉取最新代码")
        except Exception as e:
            print(f"⚠️ 拉取代码失败: {e}")
        
        return True
    
    def _select_and_branch(self, feature_name: str) -> str:
        """2️⃣ 选择与建枝阶段"""
        print("\n2️⃣ 选择与建枝阶段")
        
        # 生成分支名称
        date_str = datetime.now().strftime("%Y%m%d")
        branch_name = f"feature/{feature_name}_{date_str}"
        
        # 检查分支是否已存在
        try:
            result = subprocess.run(['git', 'branch', '--list', branch_name], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.stdout.strip():
                print(f"❌ 分支 {branch_name} 已存在")
                return None
        except Exception as e:
            print(f"❌ 分支检查失败: {e}")
            return None
        
        # 创建并切换到新分支
        try:
            subprocess.run(['git', 'checkout', '-b', branch_name], 
                          cwd=self.project_root, check=True)
            print(f"✅ 已创建并切换到分支: {branch_name}")
        except Exception as e:
            print(f"❌ 创建分支失败: {e}")
            return None
        
        return branch_name
    
    def _record_task(self, feature_name: str, description: str, branch_name: str) -> str:
        """记录任务到iteration_log.json"""
        print("\n📝 记录任务信息")
        
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        task_data = {
            "id": task_id,
            "feature_name": feature_name,
            "description": description,
            "branch_name": branch_name,
            "status": "in_progress",
            "phase": "implement",
            "created_at": datetime.now().isoformat(),
            "definition_of_done": [
                "功能代码实现完成",
                "技术测试通过（无报错、无崩溃）",
                "效果测试通过（性能不下降）",
                "文档更新完成",
                "用户验证通过"
            ]
        }
        
        # 读取现有日志
        if self.iteration_log.exists():
            with open(self.iteration_log, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        else:
            log_data = {"tasks": [], "history": []}
        
        # 添加新任务
        log_data["tasks"].append(task_data)
        
        # 保存日志
        with open(self.iteration_log, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 任务已记录: {task_id}")
        return task_id
    
    def complete_task(self, task_id: str, success: bool = True):
        """完成任务 - 合并或废弃分支"""
        print(f"\n🎯 完成任务: {task_id}")
        
        # 读取任务信息
        if not self.iteration_log.exists():
            print("❌ 找不到任务记录")
            return False
        
        with open(self.iteration_log, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        # 找到任务
        task = None
        for t in log_data["tasks"]:
            if t["id"] == task_id:
                task = t
                break
        
        if not task:
            print(f"❌ 找不到任务: {task_id}")
            return False
        
        branch_name = task["branch_name"]
        
        if success:
            # 6️⃣ 验证与合并 - 成功路径
            print("✅ 用户验证通过，合并到主分支")
            
            try:
                # 切换到主分支
                subprocess.run(['git', 'checkout', 'main'], cwd=self.project_root, check=True)
                
                # 合并分支
                subprocess.run(['git', 'merge', branch_name], cwd=self.project_root, check=True)
                
                # 删除特性分支
                subprocess.run(['git', 'branch', '-d', branch_name], cwd=self.project_root, check=True)
                
                print(f"✅ 分支 {branch_name} 已合并并删除")
                
                # 更新任务状态
                task["status"] = "completed"
                task["completed_at"] = datetime.now().isoformat()
                
            except Exception as e:
                print(f"❌ 合并失败: {e}")
                return False
        else:
            # 失败路径 - 废弃分支
            print("❌ 任务失败，废弃分支")
            
            try:
                # 切换到主分支
                subprocess.run(['git', 'checkout', 'main'], cwd=self.project_root, check=True)
                
                # 强制删除分支
                subprocess.run(['git', 'branch', '-D', branch_name], cwd=self.project_root, check=True)
                
                print(f"✅ 分支 {branch_name} 已废弃删除")
                
                # 更新任务状态
                task["status"] = "failed"
                task["failed_at"] = datetime.now().isoformat()
                
            except Exception as e:
                print(f"❌ 废弃分支失败: {e}")
                return False
        
        # 7️⃣ 确认与清理
        # 移动到历史记录
        log_data["history"].append(task)
        log_data["tasks"] = [t for t in log_data["tasks"] if t["id"] != task_id]
        
        # 保存更新
        with open(self.iteration_log, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        print("✅ 任务完成，记录已更新")
        return True
    
    def list_active_tasks(self):
        """列出当前活跃任务"""
        if not self.iteration_log.exists():
            print("📭 暂无活跃任务")
            return
        
        with open(self.iteration_log, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        active_tasks = log_data.get("tasks", [])
        
        if not active_tasks:
            print("📭 暂无活跃任务")
            return
        
        print("📋 当前活跃任务:")
        for task in active_tasks:
            print(f"  🎯 {task['id']}: {task['feature_name']}")
            print(f"     分支: {task['branch_name']}")
            print(f"     状态: {task['status']} - {task['phase']}")
            print(f"     创建: {task['created_at'][:19]}")
            print()

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python start_task.py start <功能名> <描述>  # 启动新任务")
        print("  python start_task.py complete <任务ID> [success/fail]  # 完成任务")
        print("  python start_task.py list  # 列出活跃任务")
        return
    
    project_root = os.getcwd()
    starter = TaskStarter(project_root)
    
    command = sys.argv[1]
    
    if command == "start":
        if len(sys.argv) < 4:
            print("❌ 请提供功能名和描述")
            return
        
        feature_name = sys.argv[2]
        description = sys.argv[3]
        starter.start_new_task(feature_name, description)
        
    elif command == "complete":
        if len(sys.argv) < 3:
            print("❌ 请提供任务ID")
            return
        
        task_id = sys.argv[2]
        success = len(sys.argv) < 4 or sys.argv[3] != "fail"
        starter.complete_task(task_id, success)
        
    elif command == "list":
        starter.list_active_tasks()
        
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == "__main__":
    main()
