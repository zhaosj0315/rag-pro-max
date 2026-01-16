import json
import os
from datetime import datetime
import threading

# 使用 JSONL 格式 (每行一个JSON对象)，性能更好，适合大数据量
AUDIT_LOG_PATH = "app_logs/audit_security.jsonl"

class AuditLogger:
    _lock = threading.Lock()

    @staticmethod
    def log(user, action, details, action_type="GENERIC", status="success", ip=None, browser=None, diff=None):
        """
        [v6.6.6] 企业级全量审计引擎
        :param user: 操作用户名
        :param action: 动作简称
        :param details: 业务详情
        :param action_type: 动作分类 (AUTH, KB_MGMT, DATA_PROCESS, ADMIN, SECURITY, CRAWL, PREVIEW)
        :param status: 状态 (success, failed, warning, intercepted)
        :param ip: 客户端IP
        :param browser: UA信息
        :param diff: 变更对比字典 {'old': ..., 'new': ...}
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user or "guest",
            "action_type": action_type,
            "action": action,
            "details": details,
            "status": status,
            "ip": ip or "unknown",
            "ua": browser or "unknown",
            "diff": diff # 存储变更前后对比
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