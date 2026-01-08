import json
import os
from src.auth.user_auth import load_users

SHARING_CONFIG_PATH = "config/kb_sharing.json"

def load_sharing_config():
    if os.path.exists(SHARING_CONFIG_PATH):
        try:
            with open(SHARING_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_sharing_config(config):
    with open(SHARING_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def get_visible_kbs(username, role, all_kbs):
    """
    根据权限过滤可见的知识库
    规则：
    1. Admin 可见全部
    2. 用户可见：自己拥有的 + 被显式分享给自己的 + 全局公开的
    3. 访客可见：全局公开的
    """
    if role == "admin":
        return all_kbs
        
    sharing_config = load_sharing_config()
    public_kbs = sharing_config.get("public_kbs", [])
    
    if role == "guest":
        return [kb for kb in all_kbs if kb in public_kbs]
    
    # 注册用户逻辑
    users = load_users()
    user_info = users.get(username, {})
    
    # 获取属于该用户的库 (通过 manifest 检查或历史配置)
    # 此处简化逻辑：admin可以授权白名单给用户
    whitelist = user_info.get("kb_whitelist", [])
    
    # 如果是用户自己创建的库（此处假设我们可以从 manifest 读取 owner，后续在处理器中加入）
    # 为兼容现有系统，先以白名单和公开库为主
    visible = []
    for kb in all_kbs:
        if kb in public_kbs or kb in whitelist:
            visible.append(kb)
            
    return visible

def set_kb_public(kb_name, is_public=True):
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
