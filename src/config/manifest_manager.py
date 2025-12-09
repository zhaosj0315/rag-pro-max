"""知识库清单管理器"""

import os
import json
from typing import Dict, List
from datetime import datetime


class ManifestManager:
    """知识库清单管理器"""
    
    MANIFEST_FILE = "manifest.json"
    
    @classmethod
    def get_path(cls, persist_dir: str) -> str:
        """获取清单文件路径"""
        return os.path.join(persist_dir, cls.MANIFEST_FILE)
    
    @classmethod
    def load(cls, persist_dir: str) -> Dict:
        """加载知识库清单"""
        path = cls.get_path(persist_dir)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"files": [], "embed_model": "Unknown"}
    
    @classmethod
    def save(cls, persist_dir: str, files: List[Dict], embed_model: str = "Unknown") -> bool:
        """保存知识库清单"""
        try:
            data = {
                "files": files,
                "embed_model": embed_model,
                "updated_at": datetime.now().isoformat()
            }
            path = cls.get_path(persist_dir)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    @classmethod
    def update(cls, persist_dir: str, new_files: List[Dict], 
               is_append: bool = False, embed_model: str = "Unknown") -> bool:
        """更新知识库清单"""
        try:
            if is_append:
                manifest = cls.load(persist_dir)
                files = manifest.get("files", [])
                files.extend(new_files)
            else:
                files = new_files
            
            return cls.save(persist_dir, files, embed_model)
        except Exception:
            return False
