"""
清单管理器 - 最小实现
"""

import json
import os

class ManifestManager:
    """清单管理器"""
    
    def __init__(self):
        pass
    
    def get_manifest(self):
        """获取清单"""
        return {'files': []}
    
    @staticmethod
    def load(db_path):
        """静态加载方法"""
        manifest_file = os.path.join(db_path, "manifest.json")
        if os.path.exists(manifest_file):
            try:
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {'files': []}
    
    @staticmethod
    def save(db_path, files, embed_model=None):
        """静态保存方法 - 兼容原版本参数"""
        try:
            os.makedirs(db_path, exist_ok=True)
            manifest_file = os.path.join(db_path, "manifest.json")
            
            manifest = {
                'files': files if isinstance(files, list) else [],
                'embed_model': embed_model or 'Unknown',
                'created_time': str(os.path.getctime(db_path)) if os.path.exists(db_path) else '',
                'file_count': len(files) if isinstance(files, list) else 0
            }
            
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存清单失败: {e}")
