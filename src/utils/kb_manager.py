"""
知识库管理模块 - 管理知识库的创建、重命名、删除等操作
"""
import os
import json
import time


def rename_kb(old_name: str, new_name: str, base_path: str, history_dir: str = "chat_histories"):
    """
    重命名知识库
    
    Args:
        old_name: 旧名称
        new_name: 新名称
        base_path: 知识库根目录
        history_dir: 对话历史目录
    
    Raises:
        FileExistsError: 如果新名称已存在
    """
    new_path = os.path.join(base_path, new_name)
    if os.path.exists(new_path):
        raise FileExistsError(f"知识库 '{new_name}' 已存在。")
    
    # 重命名知识库目录
    old_path = os.path.join(base_path, old_name)
    if os.path.exists(old_path):
        os.rename(old_path, new_path)
    
    # 重命名对话历史
    old_hist = os.path.join(history_dir, f"{old_name}.json")
    new_hist = os.path.join(history_dir, f"{new_name}.json")
    if os.path.exists(old_hist):
        os.rename(old_hist, new_hist)


def get_existing_kbs(root_path: str) -> list:
    """
    获取所有已存在的知识库列表（按修改时间倒序）
    
    Args:
        root_path: 知识库根目录
    
    Returns:
        list: 知识库名称列表
    """
    if not os.path.exists(root_path):
        os.makedirs(root_path)
    
    dirs = [d for d in os.listdir(root_path) 
            if os.path.isdir(os.path.join(root_path, d))]
    
    # 按修改时间倒序排序
    dirs.sort(key=lambda x: os.path.getmtime(os.path.join(root_path, x)), reverse=True)
    
    return dirs


def delete_kb(kb_name: str, base_path: str, history_dir: str = "chat_histories") -> bool:
    """
    删除知识库
    
    Args:
        kb_name: 知识库名称
        base_path: 知识库根目录
        history_dir: 对话历史目录
    
    Returns:
        bool: 是否删除成功
    """
    try:
        import shutil
        
        # 删除知识库目录
        kb_path = os.path.join(base_path, kb_name)
        if os.path.exists(kb_path):
            shutil.rmtree(kb_path)
        
        # 删除对话历史
        hist_path = os.path.join(history_dir, f"{kb_name}.json")
        if os.path.exists(hist_path):
            os.remove(hist_path)
        
        return True
    except Exception as e:
        print(f"❌ 删除知识库失败: {e}")
        return False


def auto_save_kb_info(db_path: str, embed_model: str) -> bool:
    """
    为知识库自动保存维度信息
    
    Args:
        db_path: 知识库路径
        embed_model: 嵌入模型名称
    
    Returns:
        bool: 是否保存成功
    """
    try:
        kb_info_file = os.path.join(db_path, ".kb_info.json")
        
        if not os.path.exists(kb_info_file):
            # 根据模型名称推断维度
            if "small" in embed_model:
                dim = 512
            elif "base" in embed_model:
                dim = 768
            else:
                dim = 1024
            
            kb_info = {
                "embedding_model": embed_model,
                "embedding_dim": dim,
                "created_at": time.time()
            }
            
            with open(kb_info_file, 'w') as f:
                json.dump(kb_info, f)
            
            print(f"✅ 已为知识库保存信息: {embed_model} ({dim}D)")
            return True
        else:
            print(f"ℹ️ KB 信息已存在")
            return True
            
    except Exception as e:
        print(f"❌ 保存 KB 信息失败: {e}")
        return False


def get_kb_info(db_path: str) -> dict:
    """
    获取知识库信息
    
    Args:
        db_path: 知识库路径
    
    Returns:
        dict: 知识库信息，包含 embedding_model, embedding_dim, created_at
    """
    kb_info_file = os.path.join(db_path, ".kb_info.json")
    
    if os.path.exists(kb_info_file):
        try:
            with open(kb_info_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 读取 KB 信息失败: {e}")
    
    return {}


def kb_exists(kb_name: str, base_path: str) -> bool:
    """
    检查知识库是否存在
    
    Args:
        kb_name: 知识库名称
        base_path: 知识库根目录
    
    Returns:
        bool: 是否存在
    """
    kb_path = os.path.join(base_path, kb_name)
    return os.path.exists(kb_path)
