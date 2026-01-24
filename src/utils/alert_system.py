"""
智能告警系统
监控系统状态并发送告警通知
"""

import os
import json
import time
import psutil
import threading
import subprocess
import platform
from datetime import datetime, timedelta
from typing import Dict, List, Callable
import logging  # 允许使用 - 系统告警专用

try:
    import plyer
    DESKTOP_NOTIFICATIONS = True
except ImportError:
    DESKTOP_NOTIFICATIONS = False

class AlertSystem:
    def __init__(self):
        self.config_file = "config/alert_config.json"
        self.alert_history_file = "config/alert_history.json"
        self.monitoring = False
        self.monitor_thread = None
        self.callbacks = []
        
        # 默认配置
        self.default_config = {
            'cpu_threshold': 85,
            'memory_threshold': 90,
            'disk_threshold': 95,
            'check_interval': 5,  # 秒
            'cooldown_period': 300,  # 5分钟冷却
            'enable_desktop_notifications': True,
            'enable_console_alerts': True,
            'enable_log_alerts': True,
            'alert_levels': {
                'warning': {'cpu': 75, 'memory': 80, 'disk': 85},
                'critical': {'cpu': 90, 'memory': 95, 'disk': 98}
            }
        }
        
        self.load_config()
        self.alert_history = self.load_alert_history()
        
    def load_config(self):
        """加载告警配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = self.default_config.copy()
        else:
            self.config = self.default_config.copy()
            self.save_config()
    
    def save_config(self):
        """保存告警配置"""
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def load_alert_history(self) -> List:
        """加载告警历史"""
        if os.path.exists(self.alert_history_file):
            try:
                with open(self.alert_history_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_alert_history(self):
        """保存告警历史"""
        os.makedirs(os.path.dirname(self.alert_history_file), exist_ok=True)
        with open(self.alert_history_file, 'w') as f:
            json.dump(self.alert_history, f)
    
    def add_callback(self, callback: Callable):
        """添加告警回调函数"""
        self.callbacks.append(callback)
    
    def check_system_status(self) -> Dict:
        """检查系统状态"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available': memory.available / (1024**3),
            'disk_percent': disk.percent,
            'disk_free': disk.free / (1024**3)
        }
    
    def evaluate_alerts(self, status: Dict) -> List[Dict]:
        """评估是否需要告警"""
        alerts = []
        
        # CPU告警
        if status['cpu_percent'] >= self.config['alert_levels']['critical']['cpu']:
            alerts.append({
                'type': 'cpu',
                'level': 'critical',
                'message': f"CPU使用率危险: {status['cpu_percent']:.1f}%",
                'value': status['cpu_percent'],
                'threshold': self.config['alert_levels']['critical']['cpu']
            })
        elif status['cpu_percent'] >= self.config['alert_levels']['warning']['cpu']:
            alerts.append({
                'type': 'cpu',
                'level': 'warning', 
                'message': f"CPU使用率较高: {status['cpu_percent']:.1f}%",
                'value': status['cpu_percent'],
                'threshold': self.config['alert_levels']['warning']['cpu']
            })
        
        # 内存告警
        if status['memory_percent'] >= self.config['alert_levels']['critical']['memory']:
            alerts.append({
                'type': 'memory',
                'level': 'critical',
                'message': f"内存使用率危险: {status['memory_percent']:.1f}%",
                'value': status['memory_percent'],
                'threshold': self.config['alert_levels']['critical']['memory']
            })
        elif status['memory_percent'] >= self.config['alert_levels']['warning']['memory']:
            alerts.append({
                'type': 'memory',
                'level': 'warning',
                'message': f"内存使用率较高: {status['memory_percent']:.1f}%",
                'value': status['memory_percent'],
                'threshold': self.config['alert_levels']['warning']['memory']
            })
        
        # 磁盘告警
        if status['disk_percent'] >= self.config['alert_levels']['critical']['disk']:
            alerts.append({
                'type': 'disk',
                'level': 'critical',
                'message': f"磁盘空间不足: {status['disk_percent']:.1f}%",
                'value': status['disk_percent'],
                'threshold': self.config['alert_levels']['critical']['disk']
            })
        elif status['disk_percent'] >= self.config['alert_levels']['warning']['disk']:
            alerts.append({
                'type': 'disk',
                'level': 'warning',
                'message': f"磁盘空间较少: {status['disk_percent']:.1f}%",
                'value': status['disk_percent'],
                'threshold': self.config['alert_levels']['warning']['disk']
            })
        
        return alerts
    
    def should_send_alert(self, alert: Dict) -> bool:
        """检查是否应该发送告警（考虑冷却期）"""
        now = datetime.now()
        cooldown = timedelta(seconds=self.config['cooldown_period'])
        
        # 检查相同类型的告警是否在冷却期内
        for history_alert in reversed(self.alert_history):
            alert_time = datetime.fromisoformat(history_alert['timestamp'])
            if (now - alert_time) < cooldown:
                if (history_alert['type'] == alert['type'] and 
                    history_alert['level'] == alert['level']):
                    return False
        
        return True
    
    def send_alert(self, alert: Dict, status: Dict):
        """发送告警"""
        if not self.should_send_alert(alert):
            return
        
        alert_record = {
            'timestamp': datetime.now().isoformat(),
            'type': alert['type'],
            'level': alert['level'],
            'message': alert['message'],
            'value': alert['value'],
            'threshold': alert['threshold'],
            'system_status': status
        }
        
        # 记录告警历史
        self.alert_history.append(alert_record)
        if len(self.alert_history) > 100:  # 保持最近100条
            self.alert_history = self.alert_history[-100:]
        self.save_alert_history()
        
        # 发送不同类型的通知
        if self.config['enable_console_alerts']:
            self._send_console_alert(alert_record)
        
        if self.config['enable_desktop_notifications'] and DESKTOP_NOTIFICATIONS:
            self._send_desktop_notification(alert_record)
        
        if self.config['enable_log_alerts']:
            self._send_log_alert(alert_record)
        
        # 调用回调函数
        for callback in self.callbacks:
            try:
                callback(alert_record)
            except Exception as e:
                logging.error(f"告警回调函数执行失败: {e}")
    
    def _send_console_alert(self, alert: Dict):
        """发送控制台告警"""
        level_icons = {'warning': '⚠️', 'critical': '🚨'}
        icon = level_icons.get(alert['level'], '📢')
        
        logging.info(f"\n{icon} 系统告警 [{alert['level'].upper()}]")
        logging.info(f"时间: {alert['timestamp']}")
        logging.info(f"类型: {alert['type']}")
        logging.info(f"消息: {alert['message']}")
        logging.info(f"当前值: {alert['value']:.1f}% (阈值: {alert['threshold']}%)")
        logging.info("-" * 50)
    
    def _send_desktop_notification(self, alert: Dict):
        """发送桌面通知"""
        try:
            level_icons = {'warning': '⚠️', 'critical': '🚨'}
            icon = level_icons.get(alert['level'], '📢')
            title = f"{icon} RAG Pro Max 系统告警"
            message = alert['message']
            
            # macOS 优先使用原生通知 (避免 plyer 依赖问题)
            if platform.system() == 'Darwin':
                try:
                    # 转义双引号以防止 AppleScript 语法错误
                    safe_message = message.replace('"', '\\"')
                    safe_title = title.replace('"', '\\"')
                    script = f'display notification "{safe_message}" with title "{safe_title}"'
                    subprocess.run(['osascript', '-e', script], check=True)
                    return # 成功发送后直接返回
                except Exception as mac_e:
                    logging.warning(f"macOS原生通知失败，尝试使用plyer: {mac_e}")

            # 其他系统或 macOS 失败后尝试使用 plyer
            try:
                plyer.notification.notify(
                    title=title,
                    message=message,
                    timeout=10
                )
            except Exception as e:
                logging.error(f"桌面通知发送失败: {e}")
        except Exception as e:
            logging.error(f"发送通知过程发生错误: {e}")
    
    def _send_log_alert(self, alert: Dict):
        """发送日志告警"""
        level_map = {'warning': logging.WARNING, 'critical': logging.CRITICAL}
        log_level = level_map.get(alert['level'], logging.INFO)
        
        logging.log(log_level, f"系统告警: {alert['message']} (当前值: {alert['value']:.1f}%)")
    
    def start_monitoring(self):
        """开始监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logging.info("告警系统监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logging.info("告警系统监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                status = self.check_system_status()
                alerts = self.evaluate_alerts(status)
                
                for alert in alerts:
                    self.send_alert(alert, status)
                
                time.sleep(self.config['check_interval'])
                
            except Exception as e:
                logging.error(f"告警监控循环错误: {e}")
                time.sleep(5)
    
    def get_alert_summary(self) -> Dict:
        """获取告警摘要"""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)
        
        recent_alerts = [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert['timestamp']) > last_24h
        ]
        
        summary = {
            'total_alerts_24h': len(recent_alerts),
            'critical_alerts_24h': len([a for a in recent_alerts if a['level'] == 'critical']),
            'warning_alerts_24h': len([a for a in recent_alerts if a['level'] == 'warning']),
            'most_common_type': None,
            'last_alert': self.alert_history[-1] if self.alert_history else None
        }
        
        if recent_alerts:
            type_counts = {}
            for alert in recent_alerts:
                type_counts[alert['type']] = type_counts.get(alert['type'], 0) + 1
            summary['most_common_type'] = max(type_counts, key=type_counts.get)
        
        return summary

# 全局告警系统实例
_alert_system = None

def get_alert_system() -> AlertSystem:
    """获取告警系统实例"""
    global _alert_system
    if _alert_system is None:
        _alert_system = AlertSystem()
    return _alert_system
