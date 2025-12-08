"""
配置管理模块 - 统一管理应用配置和知识库清单
"""
import os
import json
from datetime import datetime


# 配置文件路径
CONFIG_FILE = "app_config.json"


def load_config() -> dict:
    """
    加载应用配置
    
    Returns:
        dict: 配置字典，如果文件不存在或损坏则返回空字典
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 配置文件加载失败: {e}")
    return {}


def save_config(config_data: dict) -> bool:
    """
    保存应用配置（增量更新）
    
    Args:
        config_data: 要保存的配置数据
    
    Returns:
        bool: 是否保存成功
    """
    try:
        old_config = load_config()
        old_config.update(config_data)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(old_config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ 配置保存失败: {e}")
        return False


def get_manifest_path(persist_dir: str) -> str:
    """
    获取知识库清单文件路径
    
    Args:
        persist_dir: 知识库存储目录
    
    Returns:
        str: 清单文件路径
    """
    return os.path.join(persist_dir, "manifest.json")


def load_manifest(persist_dir: str) -> dict:
    """
    加载知识库清单
    
    Args:
        persist_dir: 知识库存储目录
    
    Returns:
        dict: 清单数据，包含 files 和 embed_model
    """
    m_path = get_manifest_path(persist_dir)
    if os.path.exists(m_path):
        try:
            with open(m_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 清单加载失败: {e}")
    
    return {"files": [], "embed_model": "Unknown"}


def update_manifest(persist_dir: str, new_files_info: list, is_append: bool = False, embed_model: str = "Unknown") -> bool:
    """
    更新知识库清单
    
    Args:
        persist_dir: 知识库存储目录
        new_files_info: 新文件信息列表
        is_append: 是否追加模式（True）还是新建模式（False）
        embed_model: 嵌入模型名称
    
    Returns:
        bool: 是否更新成功
    """
    try:
        if is_append:
            manifest = load_manifest(persist_dir)
        else:
            manifest = {
                "files": [],
                "created_at": str(datetime.now())
            }
        
        manifest['embed_model'] = embed_model
        
        # 合并文件信息（去重）
        existing_map = {f['name']: f for f in manifest['files']}
        for f in new_files_info:
            existing_map[f['name']] = f
        
        manifest['files'] = list(existing_map.values())
        manifest['last_updated'] = str(datetime.now())
        
        # 确保目录存在
        if not os.path.exists(persist_dir):
            os.makedirs(persist_dir)
        
        # 保存清单
        with open(get_manifest_path(persist_dir), 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=4, ensure_ascii=False)
        
        return True
        
    except Exception as e:
        print(f"❌ 清单更新失败: {e}")
        return False


def get_config_value(key: str, default=None):
    """
    获取配置项的值
    
    Args:
        key: 配置键
        default: 默认值
    
    Returns:
        配置值或默认值
    """
    config = load_config()
    return config.get(key, default)


def set_config_value(key: str, value) -> bool:
    """
    设置单个配置项
    
    Args:
        key: 配置键
        value: 配置值
    
    Returns:
        bool: 是否设置成功
    """
    return save_config({key: value})
