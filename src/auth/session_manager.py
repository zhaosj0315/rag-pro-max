import json
import os
import uuid
import time
from datetime import datetime, timedelta
from src.auth.user_auth import load_users

SHARING_CONFIG_PATH = "config/kb_sharing.json"
SESSION_CONFIG_PATH = "config/sessions.json"
DEFAULT_SESSION_DAYS = 7

# ==================== Session Token Management ====================

def load_session_store():
    if os.path.exists(SESSION_CONFIG_PATH):
        try:
            with open(SESSION_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"sessions": {}, "user_settings": {}}
    return {"sessions": {}, "user_settings": {}}

def save_session_store(store):
    os.makedirs(os.path.dirname(SESSION_CONFIG_PATH), exist_ok=True)
    with open(SESSION_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(store, f, indent=4, ensure_ascii=False)

def create_session(username):
    """创建新会话，返回 Token"""
    store = load_session_store()
    
    # 获取用户设置或默认设置
    user_settings = store.get("user_settings", {})
    # 优先使用用户特定设置，否则使用全局设置，最后使用代码默认值
    days = user_settings.get(username, user_settings.get("global_default", DEFAULT_SESSION_DAYS))
    
    token = str(uuid.uuid4())
    expiry = datetime.now() + timedelta(days=days)
    
    if "sessions" not in store:
        store["sessions"] = {}

    store["sessions"][token] = {
        "username": username,
        "expiry": expiry.isoformat(),
        "created_at": datetime.now().isoformat()
    }
    
    # 简单的垃圾回收
    _cleanup_expired_sessions(store)
    
    save_session_store(store)
    return token, days

def validate_session(token):
    """验证 Token 有效性"""
    if not token: return None
    store = load_session_store()
    session = store.get("sessions", {}).get(token)
    
    if not session:
        return None
        
    try:
        expiry = datetime.fromisoformat(session["expiry"])
        if datetime.now() > expiry:
            if token in store["sessions"]:
                del store["sessions"][token]
                save_session_store(store)
            return None
    except:
        return None
        
    return session["username"]

def revoke_user_sessions(username):
    """注销用户所有会话"""
    store = load_session_store()
    if "sessions" not in store: return 0
    
    tokens_to_remove = [k for k, v in store["sessions"].items() if v["username"] == username]
    for t in tokens_to_remove:
        del store["sessions"][t]
    save_session_store(store)
    return len(tokens_to_remove)

def get_session_settings():
    """获取会话配置"""
    store = load_session_store()
    return store.get("user_settings", {})

def set_session_setting(username, days):
    """设置会话时长"""
    store = load_session_store()
    if "user_settings" not in store:
        store["user_settings"] = {}
    
    if username == "global_default":
        store["user_settings"]["global_default"] = days
    else:
        store["user_settings"][username] = days
    save_session_store(store)

def _cleanup_expired_sessions(store):
    """清理过期会话"""
    if "sessions" not in store: return
    now = datetime.now()
    expired = []
    for token, info in store["sessions"].items():
        try:
            if now > datetime.fromisoformat(info["expiry"]):
                expired.append(token)
        except:
            expired.append(token)
    for t in expired:
        del store["sessions"][t]

# ==================== Existing Sharing Logic ====================

def load_sharing_config():
    """加载知识库共享配置"""
    if os.path.exists(SHARING_CONFIG_PATH):
        try:
            with open(SHARING_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"public_kbs": []}
    return {"public_kbs": []}

def save_sharing_config(config):
    """保存知识库共享配置"""
    os.makedirs(os.path.dirname(SHARING_CONFIG_PATH), exist_ok=True)
    with open(SHARING_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def set_kb_public(kb_name, is_public=True):
    """设置知识库是否公开"""
    config = load_sharing_config()
    public_list = config.get("public_kbs", [])
    if is_public:
        if kb_name not in public_list:
            public_list.append(kb_name)
    else:
        if kb_name in public_list:
            public_list.remove(kb_name)
    config["public_kbs"] = public_list
    save_sharing_config(config)

def get_visible_kbs(username, role, all_kbs):
    """
    根据权限过滤可见的知识库
    规则：
    1. Admin 可见全部
    2. 用户可见：自己拥有的 + 被显式分享给自己的 + 被分享给所属角色的 + 全局公开的
    3. 访客可见：全局公开的 + 被分享给 guest 角色的
    """
    if role == "admin":
        return all_kbs
        
    sharing_config = load_sharing_config()
    public_kbs = sharing_config.get("public_kbs", [])
    role_sharing = sharing_config.get("role_sharing", {})
    # 属于该角色的共享库
    shared_to_role = role_sharing.get(role, [])
    
    # 注册用户逻辑
    users = load_users()
    user_info = users.get(username, {})
    whitelist = user_info.get("kb_whitelist", [])
    
    visible = []
    for kb in all_kbs:
        # 1. 全局公开
        if kb in public_kbs:
            visible.append(kb)
            continue
        # 2. 属于该角色的
        if kb in shared_to_role:
            visible.append(kb)
            continue
        # 3. 显式分享给个人的
        if kb in whitelist:
            visible.append(kb)
            continue
        # 4. 物理所有权
        if kb.startswith(f"{username}_"):
            visible.append(kb)
            
    return visible

def get_user_storage_usage(username):
    """计算用户名下所有知识库的总物理占用 (Bytes)"""
    kb_base = os.path.join(os.getcwd(), "vector_db_storage")
    total_size = 0
    if not os.path.exists(kb_base):
        return 0
        
    for d in os.listdir(kb_base):
        # 匹配以 username_ 开头的目录
        if d.startswith(f"{username}_"):
            kb_path = os.path.join(kb_base, d)
            for root, dirs, files in os.walk(kb_path):
                for f in files:
                    fp = os.path.join(root, f)
                    if os.path.exists(fp):
                        total_size += os.path.getsize(fp)
    return total_size

def format_size(bytes):
    """格式化字节数为人类可读格式"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} TB"