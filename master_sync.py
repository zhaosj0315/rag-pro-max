#!/usr/bin/env python3
"""
RAG Pro Max 完整项目同步工具
整合代码同步、文档同步和版本统一功能
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
import logging

class ProjectSyncMaster:
    """项目同步主控制器"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        log_dir = self.project_root / "sync_logs"
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"master_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_script(self, script_name: str) -> dict:
        """运行同步脚本"""
        script_path = self.project_root / script_name
        if not script_path.exists():
            self.logger.error(f"脚本不存在: {script_name}")
            return {"success": False, "error": f"脚本不存在: {script_name}"}
        
        try:
            self.logger.info(f"执行脚本: {script_name}")
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            self.logger.error(f"执行脚本失败 {script_name}: {e}")
            return {"success": False, "error": str(e)}
    
    def create_sync_summary(self, results: dict) -> str:
        """创建同步总结报告"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        summary = f"""
# RAG Pro Max 完整项目同步报告
同步时间: {timestamp}

## 同步执行结果

### 1. 版本统一 {'✅' if results.get('version_unify', {}).get('success') else '❌'}
"""
        
        if results.get('version_unify', {}).get('success'):
            summary += "- 版本号已统一为 v2.4.7\n"
            summary += "- 所有文件版本一致性验证通过\n"
        else:
            summary += "- 版本统一失败\n"
            if 'error' in results.get('version_unify', {}):
                summary += f"- 错误: {results['version_unify']['error']}\n"
        
        summary += f"""
### 2. 代码库同步 {'✅' if results.get('codebase_sync', {}).get('success') else '❌'}
"""
        
        if results.get('codebase_sync', {}).get('success'):
            summary += "- 四层架构验证完成\n"
            summary += "- 代码备份已创建\n"
            summary += "- 文件结构分析完成\n"
        else:
            summary += "- 代码库同步失败\n"
            if 'error' in results.get('codebase_sync', {}):
                summary += f"- 错误: {results['codebase_sync']['error']}\n"
        
        summary += f"""
### 3. 文档逻辑同步 {'✅' if results.get('doc_sync', {}).get('success') else '❌'}
"""
        
        if results.get('doc_sync', {}).get('success'):
            summary += "- 文档完整性验证通过\n"
            summary += "- 架构文档与代码结构对齐\n"
            summary += "- 功能描述同步完成\n"
        else:
            summary += "- 文档同步失败\n"
            if 'error' in results.get('doc_sync', {}):
                summary += f"- 错误: {results['doc_sync']['error']}\n"
        
        # 添加项目统计信息
        summary += f"""
## 项目统计信息
- 项目根目录: {self.project_root}
- 同步脚本数量: 3 个
- 成功执行: {sum(1 for r in results.values() if r.get('success'))} 个
- 失败执行: {sum(1 for r in results.values() if not r.get('success'))} 个

## 生成的文件
- 备份目录: backups/backup_*
- 同步结果: sync_results/
- 同步日志: sync_logs/

## 下一步建议
1. 检查 sync_results/ 目录中的详细报告
2. 验证应用程序是否正常运行: `streamlit run src/apppro.py`
3. 运行测试验证功能完整性
4. 提交代码变更到版本控制系统

---
报告生成时间: {timestamp}
"""
        
        return summary
    
    def full_sync(self) -> dict:
        """执行完整项目同步"""
        self.logger.info("🚀 开始执行完整项目同步...")
        
        sync_results = {}
        
        # 1. 版本统一
        print("🔄 步骤 1/3: 统一版本号...")
        sync_results['version_unify'] = self.run_script('unify_versions.py')
        
        # 2. 代码库同步
        print("📁 步骤 2/3: 同步代码库...")
        sync_results['codebase_sync'] = self.run_script('sync_codebase.py')
        
        # 3. 文档逻辑同步
        print("📚 步骤 3/3: 同步文档逻辑...")
        sync_results['doc_sync'] = self.run_script('sync_documentation.py')
        
        # 4. 生成总结报告
        summary = self.create_sync_summary(sync_results)
        
        # 5. 保存总结报告
        sync_dir = self.project_root / "sync_results"
        sync_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_file = sync_dir / f"master_sync_summary_{timestamp}.md"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        # 6. 保存详细结果
        results_file = sync_dir / f"master_sync_results_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(sync_results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"完整同步完成! 报告保存至: {summary_file}")
        
        return {
            "sync_results": sync_results,
            "summary": summary,
            "summary_file": str(summary_file),
            "results_file": str(results_file)
        }
    
    def quick_status_check(self) -> dict:
        """快速状态检查"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "core_files": {},
            "directories": {},
            "recent_syncs": []
        }
        
        # 检查核心文件
        core_files = [
            "src/apppro.py",
            "README.md",
            "requirements.txt",
            "CHANGELOG.md"
        ]
        
        for file_name in core_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                stat = file_path.stat()
                status["core_files"][file_name] = {
                    "exists": True,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
            else:
                status["core_files"][file_name] = {"exists": False}
        
        # 检查关键目录
        key_dirs = ["src", "config", "sync_results", "sync_logs", "backups"]
        for dir_name in key_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                file_count = len(list(dir_path.rglob("*")))
                status["directories"][dir_name] = {
                    "exists": True,
                    "file_count": file_count
                }
            else:
                status["directories"][dir_name] = {"exists": False}
        
        # 检查最近的同步记录
        sync_results_dir = self.project_root / "sync_results"
        if sync_results_dir.exists():
            sync_files = list(sync_results_dir.glob("master_sync_summary_*.md"))
            sync_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for sync_file in sync_files[:3]:  # 最近3次同步
                stat = sync_file.stat()
                status["recent_syncs"].append({
                    "file": sync_file.name,
                    "timestamp": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return status

def main():
    """主函数"""
    print("🎯 RAG Pro Max 完整项目同步工具")
    print("=" * 60)
    print("基于四层架构的智能文档问答系统完整同步")
    print("=" * 60)
    
    # 初始化主控制器
    master = ProjectSyncMaster()
    
    # 显示项目信息
    print(f"📂 项目根目录: {master.project_root}")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 快速状态检查
        print("\n🔍 执行快速状态检查...")
        status = master.quick_status_check()
        
        print(f"  ✅ 核心文件: {sum(1 for f in status['core_files'].values() if f.get('exists'))} / {len(status['core_files'])}")
        print(f"  ✅ 关键目录: {sum(1 for d in status['directories'].values() if d.get('exists'))} / {len(status['directories'])}")
        print(f"  📋 历史同步: {len(status['recent_syncs'])} 次")
        
        # 执行完整同步
        print("\n🚀 开始执行完整同步...")
        result = master.full_sync()
        
        # 显示结果
        print("\n" + "=" * 60)
        print("🎉 同步完成!")
        print("=" * 60)
        
        success_count = sum(1 for r in result['sync_results'].values() if r.get('success'))
        total_count = len(result['sync_results'])
        
        print(f"📊 执行结果: {success_count}/{total_count} 成功")
        print(f"📄 总结报告: {result['summary_file']}")
        print(f"📋 详细结果: {result['results_file']}")
        
        # 显示简要总结
        print("\n📋 同步总结:")
        for step_name, step_result in result['sync_results'].items():
            status_icon = "✅" if step_result.get('success') else "❌"
            step_display = {
                'version_unify': '版本统一',
                'codebase_sync': '代码库同步', 
                'doc_sync': '文档逻辑同步'
            }
            print(f"  {status_icon} {step_display.get(step_name, step_name)}")
        
        print(f"\n🎯 项目版本: v2.4.7")
        print(f"🏗️  架构: 四层架构设计")
        print(f"📁 总文件: {status['directories'].get('src', {}).get('file_count', 'N/A')} 个源文件")
        
        print("\n🚀 下一步:")
        print("  1. 检查同步报告: sync_results/")
        print("  2. 启动应用: streamlit run src/apppro.py")
        print("  3. 验证功能完整性")
        
    except Exception as e:
        print(f"\n❌ 同步失败: {e}")
        logging.error(f"完整同步失败: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
