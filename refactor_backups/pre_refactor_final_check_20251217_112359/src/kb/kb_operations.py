"""知识库基础操作模块"""

import os
import json
import shutil
import time
from typing import List, Dict, Optional


class KBOperations:
    """知识库基础操作类"""
    
    @staticmethod
    def create_kb(kb_name: str, base_path: str) -> bool:
        """创建知识库"""
        try:
            kb_path = os.path.join(base_path, kb_name)
            if not os.path.exists(kb_path):
                os.makedirs(kb_path)
                return True
            return False
        except Exception as e:
            print(f"❌ 创建知识库失败: {e}")
            return False
    
    @staticmethod
    def delete_kb(kb_name: str, base_path: str, history_dir: str = "chat_histories") -> bool:
        """删除知识库"""
        try:
            kb_path = os.path.join(base_path, kb_name)
            if os.path.exists(kb_path):
                shutil.rmtree(kb_path)
            
            hist_path = os.path.join(history_dir, f"{kb_name}.json")
            if os.path.exists(hist_path):
                os.remove(hist_path)
            
            return True
        except Exception as e:
            print(f"❌ 删除知识库失败: {e}")
            return False
    
    @staticmethod
    def rename_kb(old_name: str, new_name: str, base_path: str, history_dir: str = "chat_histories") -> bool:
        """重命名知识库"""
        try:
            new_path = os.path.join(base_path, new_name)
            if os.path.exists(new_path):
                raise FileExistsError(f"知识库 '{new_name}' 已存在")
            
            old_path = os.path.join(base_path, old_name)
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
            
            old_hist = os.path.join(history_dir, f"{old_name}.json")
            new_hist = os.path.join(history_dir, f"{new_name}.json")
            if os.path.exists(old_hist):
                os.rename(old_hist, new_hist)
            
            return True
        except Exception as e:
            print(f"❌ 重命名知识库失败: {e}")
            return False
    
    @staticmethod
    def list_kbs(base_path: str, sort_by_time: bool = True) -> List[str]:
        """列出所有知识库"""
        if not os.path.exists(base_path):
            os.makedirs(base_path)
            return []
        
        dirs = [d for d in os.listdir(base_path) 
                if os.path.isdir(os.path.join(base_path, d))]
        
        if sort_by_time:
            dirs.sort(key=lambda x: os.path.getmtime(os.path.join(base_path, x)), reverse=True)
        else:
            dirs.sort()
        
        return dirs
    
    @staticmethod
    def kb_exists(kb_name: str, base_path: str) -> bool:
        """检查知识库是否存在"""
        kb_path = os.path.join(base_path, kb_name)
        return os.path.exists(kb_path)
    
    @staticmethod
    def save_kb_info(db_path: str, embed_model: str, embed_dim: int) -> bool:
        """保存知识库信息"""
        try:
            kb_info_file = os.path.join(db_path, ".kb_info.json")
            kb_info = {
                "embedding_model": embed_model,
                "embedding_dim": embed_dim,
                "created_at": time.time()
            }
            
            with open(kb_info_file, 'w') as f:
                json.dump(kb_info, f)
            
            return True
        except Exception as e:
            print(f"❌ 保存知识库信息失败: {e}")
            return False
    
    @staticmethod
    def load_kb_info(db_path: str) -> Optional[Dict]:
        """加载知识库信息"""
        kb_info_file = os.path.join(db_path, ".kb_info.json")
        
        if os.path.exists(kb_info_file):
            try:
                with open(kb_info_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 读取知识库信息失败: {e}")
        
        return None
