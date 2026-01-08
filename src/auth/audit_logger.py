import json
import os
from datetime import datetime
import threading

AUDIT_LOG_PATH = "app_logs/audit_security.json"

class AuditLogger:
    _lock = threading.Lock()

    @staticmethod
    def log(user, action, details, status="success"):
        """
        记录审计日志
        :param user: 操作用户名
        :param action: 动作名称 (e.g., 'LOGIN', 'EXPORT_DATA', 'UPDATE_PERMISSION')
        :param details: 详细描述
        :param status: 状态 (success/failed/warning)
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "action": action,
            "details": details,
            "status": status,
            "ip": "local" # 后续可扩展获取真实IP
        }
        
        # 确保目录存在
        os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
        
        # 线程安全写入
        with AuditLogger._lock:
            try:
                logs = []
                if os.path.exists(AUDIT_LOG_PATH):
                    with open(AUDIT_LOG_PATH, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                
                logs.insert(0, log_entry) # 最新日志在最前
                
                # 仅保留最近 1000 条日志，防止文件过大
                logs = logs[:1000]
                
                with open(AUDIT_LOG_PATH, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"Failed to write audit log: {e}")

    @staticmethod
    def get_logs():
        if os.path.exists(AUDIT_LOG_PATH):
            try:
                with open(AUDIT_LOG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
