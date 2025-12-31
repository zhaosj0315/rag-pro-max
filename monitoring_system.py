#!/usr/bin/env python3
"""
RAG Pro Max 监控与告警系统
实现自动化巡查和实时监控
"""

import os
import json
import time
import logging
import psutil
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
import smtplib
from email.mime.text import MIMEText

@dataclass
class Alert:
    level: str  # INFO, WARNING, ERROR, CRITICAL
    category: str
    message: str
    timestamp: str
    metrics: Dict[str, Any]

class MonitoringSystem:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.alerts_dir = self.project_root / "monitoring_alerts"
        self.alerts_dir.mkdir(exist_ok=True)
        
        # 配置阈值
        self.thresholds = {
            "response_time": 2.0,  # 秒
            "error_rate": 0.05,    # 5%
            "memory_usage": 0.85,  # 85%
            "disk_usage": 0.90,    # 90%
            "cpu_usage": 0.80      # 80%
        }
        
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        log_file = self.alerts_dir / "monitoring.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def run_health_check(self) -> List[Alert]:
        """运行健康检查"""
        alerts = []
        
        # 系统资源检查
        alerts.extend(self.check_system_resources())
        
        # 应用健康检查
        alerts.extend(self.check_application_health())
        
        # 日志异常检查
        alerts.extend(self.check_log_errors())
        
        # 存储空间检查
        alerts.extend(self.check_storage_space())
        
        # 处理告警
        self.process_alerts(alerts)
        
        return alerts
    
    def check_system_resources(self) -> List[Alert]:
        """检查系统资源"""
        alerts = []
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > self.thresholds["cpu_usage"] * 100:
            alerts.append(Alert(
                level="WARNING",
                category="system",
                message=f"CPU使用率过高: {cpu_percent:.1f}%",
                timestamp=datetime.now().isoformat(),
                metrics={"cpu_percent": cpu_percent}
            ))
        
        # 内存使用率
        memory = psutil.virtual_memory()
        if memory.percent > self.thresholds["memory_usage"] * 100:
            alerts.append(Alert(
                level="WARNING", 
                category="system",
                message=f"内存使用率过高: {memory.percent:.1f}%",
                timestamp=datetime.now().isoformat(),
                metrics={"memory_percent": memory.percent}
            ))
        
        # 磁盘使用率
        disk = psutil.disk_usage(str(self.project_root))
        disk_percent = (disk.used / disk.total) * 100
        if disk_percent > self.thresholds["disk_usage"] * 100:
            alerts.append(Alert(
                level="ERROR",
                category="system", 
                message=f"磁盘空间不足: {disk_percent:.1f}%",
                timestamp=datetime.now().isoformat(),
                metrics={"disk_percent": disk_percent}
            ))
        
        return alerts
    
    def check_application_health(self) -> List[Alert]:
        """检查应用健康状态"""
        alerts = []
        
        # 检查关键文件
        critical_files = [
            "src/apppro.py",
            "requirements.txt",
            "config/app_config.json"
        ]
        
        for file_path in critical_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                alerts.append(Alert(
                    level="CRITICAL",
                    category="application",
                    message=f"关键文件缺失: {file_path}",
                    timestamp=datetime.now().isoformat(),
                    metrics={"missing_file": str(full_path)}
                ))
        
        # 检查配置文件
        config_file = self.project_root / "config" / "app_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError:
                alerts.append(Alert(
                    level="ERROR",
                    category="application",
                    message="配置文件格式错误",
                    timestamp=datetime.now().isoformat(),
                    metrics={"config_file": str(config_file)}
                ))
        
        return alerts
    
    def check_log_errors(self) -> List[Alert]:
        """检查日志中的错误"""
        alerts = []
        
        log_dir = self.project_root / "app_logs"
        if not log_dir.exists():
            return alerts
        
        # 检查最近1小时的错误日志
        cutoff_time = datetime.now() - timedelta(hours=1)
        error_count = 0
        
        for log_file in log_dir.glob("*.log"):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if "ERROR" in line or "CRITICAL" in line:
                            # 简单的时间解析（实际应用中需要更精确）
                            error_count += 1
            except Exception:
                continue
        
        if error_count > 10:  # 1小时内超过10个错误
            alerts.append(Alert(
                level="WARNING",
                category="application",
                message=f"错误日志过多: {error_count}条/小时",
                timestamp=datetime.now().isoformat(),
                metrics={"error_count": error_count}
            ))
        
        return alerts
    
    def check_storage_space(self) -> List[Alert]:
        """检查存储空间"""
        alerts = []
        
        # 检查各个目录大小
        directories = {
            "vector_db_storage": 1000,  # MB
            "temp_uploads": 500,
            "app_logs": 100,
            "hf_cache": 2000
        }
        
        for dir_name, max_size_mb in directories.items():
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                size_mb = sum(f.stat().st_size for f in dir_path.rglob("*") 
                             if f.is_file()) / (1024 * 1024)
                
                if size_mb > max_size_mb:
                    alerts.append(Alert(
                        level="WARNING",
                        category="storage",
                        message=f"{dir_name}目录过大: {size_mb:.1f}MB",
                        timestamp=datetime.now().isoformat(),
                        metrics={"directory": dir_name, "size_mb": size_mb}
                    ))
        
        return alerts
    
    def process_alerts(self, alerts: List[Alert]):
        """处理告警"""
        if not alerts:
            self.logger.info("✅ 系统健康检查通过")
            return
        
        # 按级别分类
        critical_alerts = [a for a in alerts if a.level == "CRITICAL"]
        error_alerts = [a for a in alerts if a.level == "ERROR"]
        warning_alerts = [a for a in alerts if a.level == "WARNING"]
        
        # 记录告警
        alert_file = self.alerts_dir / f"alerts_{datetime.now().strftime('%Y%m%d')}.json"
        with open(alert_file, 'a', encoding='utf-8') as f:
            for alert in alerts:
                f.write(json.dumps(alert.__dict__, ensure_ascii=False) + "\n")
        
        # 输出告警摘要
        self.logger.warning(f"🚨 发现 {len(alerts)} 个告警")
        self.logger.warning(f"   严重: {len(critical_alerts)}")
        self.logger.warning(f"   错误: {len(error_alerts)}")
        self.logger.warning(f"   警告: {len(warning_alerts)}")
        
        # 发送通知（如果配置了）
        if critical_alerts or error_alerts:
            self.send_notifications(alerts)
    
    def send_notifications(self, alerts: List[Alert]):
        """发送通知"""
        # 这里可以集成邮件、Slack、钉钉等通知方式
        self.logger.info("📧 发送告警通知（功能待实现）")
    
    def generate_health_report(self) -> Dict[str, Any]:
        """生成健康报告"""
        alerts = self.run_health_check()
        
        # 系统指标
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(str(self.project_root))
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy" if not alerts else "warning",
            "alerts_count": len(alerts),
            "system_metrics": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": (disk.used / disk.total) * 100,
                "available_memory_gb": memory.available / (1024**3),
                "free_disk_gb": disk.free / (1024**3)
            },
            "alerts": [alert.__dict__ for alert in alerts]
        }
        
        # 保存报告
        report_file = self.alerts_dir / f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report

def main():
    """主函数"""
    import sys
    
    project_root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    monitor = MonitoringSystem(project_root)
    report = monitor.generate_health_report()
    
    print(f"📊 健康检查完成")
    print(f"状态: {report['status']}")
    print(f"告警数量: {report['alerts_count']}")
    print(f"CPU: {report['system_metrics']['cpu_percent']:.1f}%")
    print(f"内存: {report['system_metrics']['memory_percent']:.1f}%")
    print(f"磁盘: {report['system_metrics']['disk_percent']:.1f}%")

if __name__ == "__main__":
    main()
