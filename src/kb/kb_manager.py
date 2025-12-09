"""知识库管理器 - 高级管理功能"""

import os
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from .kb_operations import KBOperations


class KBManager:
    """知识库管理器 - 提供高级管理功能"""
    
    def __init__(self, base_path: str = "vector_db_storage", history_dir: str = "chat_histories"):
        self.base_path = base_path
        self.history_dir = history_dir
        self.ops = KBOperations()
    
    def create(self, kb_name: str) -> Tuple[bool, str]:
        """创建知识库"""
        if not kb_name or not kb_name.strip():
            return False, "知识库名称不能为空"
        
        if self.ops.kb_exists(kb_name, self.base_path):
            return False, f"知识库 '{kb_name}' 已存在"
        
        success = self.ops.create_kb(kb_name, self.base_path)
        if success:
            return True, f"✅ 知识库 '{kb_name}' 创建成功"
        else:
            return False, "创建失败"
    
    def delete(self, kb_name: str) -> Tuple[bool, str]:
        """删除知识库"""
        if not self.ops.kb_exists(kb_name, self.base_path):
            return False, f"知识库 '{kb_name}' 不存在"
        
        success = self.ops.delete_kb(kb_name, self.base_path, self.history_dir)
        if success:
            return True, f"✅ 知识库 '{kb_name}' 已删除"
        else:
            return False, "删除失败"
    
    def rename(self, old_name: str, new_name: str) -> Tuple[bool, str]:
        """重命名知识库"""
        if not self.ops.kb_exists(old_name, self.base_path):
            return False, f"知识库 '{old_name}' 不存在"
        
        if self.ops.kb_exists(new_name, self.base_path):
            return False, f"知识库 '{new_name}' 已存在"
        
        success = self.ops.rename_kb(old_name, new_name, self.base_path, self.history_dir)
        if success:
            return True, f"✅ 知识库已重命名: {old_name} → {new_name}"
        else:
            return False, "重命名失败"
    
    def list_all(self, sort_by_time: bool = True) -> List[str]:
        """列出所有知识库"""
        return self.ops.list_kbs(self.base_path, sort_by_time)
    
    def exists(self, kb_name: str) -> bool:
        """检查知识库是否存在"""
        return self.ops.kb_exists(kb_name, self.base_path)
    
    def get_info(self, kb_name: str) -> Optional[Dict]:
        """获取知识库信息"""
        if not self.exists(kb_name):
            return None
        
        kb_path = os.path.join(self.base_path, kb_name)
        info = self.ops.load_kb_info(kb_path)
        
        if info:
            info['name'] = kb_name
            info['path'] = kb_path
            info['created_time'] = datetime.fromtimestamp(info.get('created_at', 0)).strftime('%Y-%m-%d %H:%M:%S')
        
        return info
    
    def save_info(self, kb_name: str, embed_model: str, embed_dim: int) -> bool:
        """保存知识库信息"""
        if not self.exists(kb_name):
            return False
        
        kb_path = os.path.join(self.base_path, kb_name)
        return self.ops.save_kb_info(kb_path, embed_model, embed_dim)
    
    def get_stats(self, kb_name: str) -> Optional[Dict]:
        """获取知识库统计信息"""
        if not self.exists(kb_name):
            return None
        
        kb_path = os.path.join(self.base_path, kb_name)
        
        stats = {
            'name': kb_name,
            'path': kb_path,
            'size': self._get_dir_size(kb_path),
            'file_count': self._count_files(kb_path),
            'modified_time': datetime.fromtimestamp(os.path.getmtime(kb_path)).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        info = self.get_info(kb_name)
        if info:
            stats.update(info)
        
        return stats
    
    def search(self, keyword: str) -> List[str]:
        """搜索知识库"""
        all_kbs = self.list_all(sort_by_time=False)
        return [kb for kb in all_kbs if keyword.lower() in kb.lower()]
    
    @staticmethod
    def _get_dir_size(path: str) -> int:
        """获取目录大小（字节）"""
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
        except Exception:
            pass
        return total
    
    @staticmethod
    def _count_files(path: str) -> int:
        """统计文件数量"""
        count = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                count += len(filenames)
        except Exception:
            pass
        return count
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
