#!/usr/bin/env python3
"""
RAG Pro Max 每日健康检查脚本
执行冒烟测试，确保核心功能正常
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path

class DailyHealthCheck:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": [],
            "summary": {"passed": 0, "failed": 0, "total": 0}
        }
    
    def run_check(self, name: str, check_func):
        """运行单个检查"""
        print(f"🔍 检查: {name}")
        start_time = time.time()
        
        try:
            result = check_func()
            status = "PASS" if result else "FAIL"
            duration = time.time() - start_time
            
            check_result = {
                "name": name,
                "status": status,
                "duration": duration,
                "details": result if isinstance(result, dict) else {}
            }
            
            self.results["checks"].append(check_result)
            
            if status == "PASS":
                self.results["summary"]["passed"] += 1
                print(f"  ✅ 通过 ({duration:.2f}s)")
            else:
                self.results["summary"]["failed"] += 1
                print(f"  ❌ 失败 ({duration:.2f}s)")
                
            self.results["summary"]["total"] += 1
            
        except Exception as e:
            print(f"  💥 异常: {e}")
            self.results["checks"].append({
                "name": name,
                "status": "ERROR",
                "duration": time.time() - start_time,
                "error": str(e)
            })
            self.results["summary"]["failed"] += 1
            self.results["summary"]["total"] += 1
    
    def check_core_files(self) -> bool:
        """检查核心文件存在性"""
        required_files = [
            "src/apppro.py",
            "requirements.txt",
            "config/app_config.json",
            "start.sh"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        return len(missing_files) == 0
    
    def check_python_imports(self) -> bool:
        """检查Python依赖导入"""
        try:
            # 测试关键依赖
            import streamlit
            import pandas
            import numpy
            return True
        except ImportError as e:
            print(f"    导入失败: {e}")
            return False
    
    def check_config_files(self) -> bool:
        """检查配置文件格式"""
        config_files = [
            "config/app_config.json",
            "config/rag_config.json"
        ]
        
        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                except json.JSONDecodeError:
                    return False
        
        return True
    
    def check_directory_structure(self) -> bool:
        """检查目录结构"""
        required_dirs = [
            "src",
            "config", 
            "tests",
            "scripts"
        ]
        
        for dir_name in required_dirs:
            if not (self.project_root / dir_name).exists():
                return False
        
        return True
    
    def check_log_directory(self) -> bool:
        """检查日志目录"""
        log_dir = self.project_root / "app_logs"
        if not log_dir.exists():
            log_dir.mkdir(exist_ok=True)
        
        # 检查是否可写
        test_file = log_dir / "health_check_test.log"
        try:
            test_file.write_text("test")
            test_file.unlink()
            return True
        except Exception:
            return False
    
    def check_storage_directories(self) -> bool:
        """检查存储目录"""
        storage_dirs = [
            "vector_db_storage",
            "temp_uploads", 
            "chat_histories"
        ]
        
        for dir_name in storage_dirs:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                dir_path.mkdir(exist_ok=True)
        
        return True
    
    def check_git_status(self) -> bool:
        """检查Git状态"""
        git_dir = self.project_root / ".git"
        if not git_dir.exists():
            return False
        
        # 检查是否有未提交的关键文件修改
        try:
            import subprocess
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            # 如果有未跟踪的重要文件，返回警告
            untracked_important = []
            for line in result.stdout.splitlines():
                if line.startswith("??") and any(ext in line for ext in [".py", ".json", ".md"]):
                    untracked_important.append(line[3:])
            
            return len(untracked_important) == 0
            
        except Exception:
            return True  # Git检查失败不影响整体健康状态
    
    def run_all_checks(self):
        """运行所有健康检查"""
        print("🏥 RAG Pro Max 每日健康检查")
        print("=" * 50)
        
        # 定义所有检查项
        checks = [
            ("核心文件完整性", self.check_core_files),
            ("Python依赖导入", self.check_python_imports),
            ("配置文件格式", self.check_config_files),
            ("目录结构完整", self.check_directory_structure),
            ("日志目录可写", self.check_log_directory),
            ("存储目录就绪", self.check_storage_directories),
            ("Git仓库状态", self.check_git_status)
        ]
        
        # 执行所有检查
        for name, check_func in checks:
            self.run_check(name, check_func)
        
        # 输出摘要
        self.print_summary()
        
        # 保存结果
        self.save_results()
        
        return self.results["summary"]["failed"] == 0
    
    def print_summary(self):
        """打印检查摘要"""
        summary = self.results["summary"]
        print("\n" + "=" * 50)
        print("📊 检查摘要")
        print(f"总计: {summary['total']}")
        print(f"通过: {summary['passed']} ✅")
        print(f"失败: {summary['failed']} ❌")
        
        success_rate = (summary['passed'] / summary['total']) * 100 if summary['total'] > 0 else 0
        print(f"成功率: {success_rate:.1f}%")
        
        if summary['failed'] == 0:
            print("\n🎉 所有检查通过！系统健康状态良好")
        else:
            print(f"\n⚠️ 发现 {summary['failed']} 个问题，请及时处理")
    
    def save_results(self):
        """保存检查结果"""
        results_dir = self.project_root / "monitoring_alerts"
        results_dir.mkdir(exist_ok=True)
        
        result_file = results_dir / f"daily_health_check_{datetime.now().strftime('%Y%m%d')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 检查结果已保存: {result_file}")

def main():
    """主函数"""
    project_root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    health_check = DailyHealthCheck(project_root)
    success = health_check.run_all_checks()
    
    # 返回适当的退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
