"""
清单管理器 - 完整实现
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any

class ManifestManager:
    """清单管理器"""
    
    def __init__(self):
        pass
    
    def get_manifest(self):
        """获取清单"""
        return {'files': []}
    
    @staticmethod
    def get_path(db_path: str) -> str:
        """获取清单文件路径"""
        return os.path.join(db_path, "manifest.json")
    
    @staticmethod
    def load(db_path: str) -> Dict[str, Any]:
        """静态加载方法"""
        manifest_file = ManifestManager.get_path(db_path)  # 使用统一的路径方法
        if os.path.exists(manifest_file):
            try:
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    # 确保必要的字段存在
                    if 'files' not in manifest:
                        manifest['files'] = []
                    if 'file_count' not in manifest:
                        manifest['file_count'] = len(manifest['files'])
                    return manifest
            except Exception as e:
                print(f"加载清单失败: {e}")
        
        return {
            'files': [],
            'file_count': 0,
            'embed_model': 'Unknown',
            'created_time': '',
            'total_size': 0
        }
    
    @staticmethod
    def save(db_path: str, files: List[Dict], embed_model: str = None) -> bool:
        """静态保存方法 - 兼容原版本参数"""
        try:
            os.makedirs(db_path, exist_ok=True)
            manifest_file = os.path.join(db_path, "manifest.json")
            
            # 计算总大小
            total_size = 0
            processed_files = []
            
            for file_info in files:
                if isinstance(file_info, dict):
                    processed_files.append(file_info)
                    # 确保size是整数
                    size = file_info.get('size', 0)
                    if isinstance(size, str):
                        try:
                            size = int(size)
                        except (ValueError, TypeError):
                            size = 0
                    total_size += size
                elif isinstance(file_info, str):
                    # 如果是文件路径字符串，转换为字典
                    file_size = 0
                    if os.path.exists(file_info):
                        file_size = os.path.getsize(file_info)
                    
                    processed_files.append({
                        'path': file_info,
                        'name': os.path.basename(file_info),
                        'size': file_size,
                        'type': os.path.splitext(file_info)[1].lower(),
                        'added_time': datetime.now().isoformat()
                    })
                    total_size += file_size
            
            manifest = {
                'files': processed_files,
                'file_count': len(processed_files),
                'embed_model': embed_model or 'Unknown',
                'created_time': datetime.now().isoformat(),
                'total_size': total_size,
                'version': '2.3.1'
            }
            
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"保存清单失败: {e}")
            return False
    
    @staticmethod
    def get_stats(db_path: str) -> Dict[str, Any]:
        """获取知识库统计信息"""
        manifest = ManifestManager.load(db_path)
        
        # 计算文档片段数（从索引文件）
        doc_count = 0
        try:
            docstore_file = os.path.join(db_path, "docstore.json")
            if os.path.exists(docstore_file):
                with open(docstore_file, 'r', encoding='utf-8') as f:
                    docstore = json.load(f)
                    doc_count = len(docstore.get('docstore/data', {}))
        except:
            pass
        
        return {
            'file_count': manifest.get('file_count', 0),
            'doc_count': doc_count,
            'total_size': manifest.get('total_size', 0),
            'embed_model': manifest.get('embed_model', 'Unknown'),
            'created_time': manifest.get('created_time', ''),
            'files': manifest.get('files', [])
        }
    
    @staticmethod
    def format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"
