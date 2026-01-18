import json
import os
from datetime import datetime
import threading

# 使用 JSONL 格式 (每行一个JSON对象)，性能更好，适合大数据量
AUDIT_LOG_PATH = "app_logs/audit_security.jsonl"

class AuditLogger:
    _lock = threading.Lock()

    @staticmethod
    def log(user, action, details, action_type="GENERIC", status="success", level="INFO", resource_id=None, cost_ms=0, ip=None, browser=None, diff=None):
        """
        [v6.8.6] 增强型审计引擎
        :param level: 风险等级 (INFO, WARNING, CRITICAL)
        :param resource_id: 关联资源ID
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user or "guest",
            "action_type": action_type,
            "action": action,
            "details": details,
            "status": status,
            "level": level,
            "resource_id": resource_id,
            "cost_ms": cost_ms,
            "ip": ip or "unknown",
            "ua": browser or "unknown",
            "diff": diff
        }
        
        # 确保目录存在
        os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
        
        # 线程安全写入 (追加模式)
        with AuditLogger._lock:
            try:
                with open(AUDIT_LOG_PATH, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
                
                # [v6.4.5] 权限自愈
                try:
                    os.chmod(AUDIT_LOG_PATH, 0o666)
                except: pass
            except Exception as e:
                print(f"Failed to write audit log: {e}")

    @staticmethod
    def get_logs(limit=1000):
        """从 JSONL 反向读取最近的日志"""
        if not os.path.exists(AUDIT_LOG_PATH):
            return []
            
        logs = []
        try:
            with open(AUDIT_LOG_PATH, 'r', encoding='utf-8') as f:
                # 倒序读取的高效方案：读出所有行再反转 (对于中型日志有效)
                lines = f.readlines()
                for line in reversed(lines):
                    if line.strip():
                        logs.append(json.loads(line))
                    if len(logs) >= limit:
                        break
            return logs
        except Exception as e:
            print(f"Read audit logs failed: {e}")
            return []

    @staticmethod
    def clear_logs():
        """物理清空审计日志 (仅限超级管理员)"""
        with AuditLogger._lock:
            try:
                if os.path.exists(AUDIT_LOG_PATH):
                    os.remove(AUDIT_LOG_PATH)
                return True
            except:
                return False