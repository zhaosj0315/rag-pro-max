"""增量更新管理器 - 支持文档增量添加，无需重建整个知识库"""

import os
import json
import hashlib
from typing import List, Dict, Optional, Set
from datetime import datetime
from pathlib import Path


class IncrementalUpdater:
    """增量更新管理器"""
    
    def __init__(self, kb_path: str):
        self.kb_path = kb_path
        self.metadata_file = os.path.join(kb_path, "incremental_metadata.json")
        self.file_hashes = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, str]:
        """加载文件哈希元数据"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_metadata(self):
        """保存文件哈希元数据"""
        os.makedirs(os.path.dirname(self.metadata_file), exist_ok=True)
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.file_hashes, f, ensure_ascii=False, indent=2)
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return ""
    
    def get_changed_files(self, file_paths: List[str]) -> Dict[str, List[str]]:
        """检测文件变化
        
        Returns:
            {
                'new': [...],      # 新文件
                'modified': [...], # 修改的文件
                'unchanged': [...] # 未变化的文件
            }
        """
        result = {'new': [], 'modified': [], 'unchanged': []}
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue
                
            current_hash = self._calculate_file_hash(file_path)
            stored_hash = self.file_hashes.get(file_path)
            
            if stored_hash is None:
                result['new'].append(file_path)
            elif stored_hash != current_hash:
                result['modified'].append(file_path)
            else:
                result['unchanged'].append(file_path)
        
        return result
    
    def mark_files_processed(self, file_paths: List[str]):
        """标记文件已处理"""
        for file_path in file_paths:
            if os.path.exists(file_path):
                self.file_hashes[file_path] = self._calculate_file_hash(file_path)
        self._save_metadata()
    
    def remove_file_record(self, file_path: str):
        """移除文件记录"""
        if file_path in self.file_hashes:
            del self.file_hashes[file_path]
            self._save_metadata()
    
    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            'total_files': len(self.file_hashes),
            'last_update': int(os.path.getmtime(self.metadata_file)) if os.path.exists(self.metadata_file) else 0
        }
