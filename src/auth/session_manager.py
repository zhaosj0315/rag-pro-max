import json
import os
from src.auth.user_auth import load_users

SHARING_CONFIG_PATH = "config/kb_sharing.json"

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