#!/usr/bin/env python3
"""
知识库服务模块 - 统一知识库操作逻辑
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path

class KnowledgeBaseService:
    """统一的知识库管理服务"""
    
    def __init__(self, storage_dir: str = "vector_db_storage"):
        self.storage_dir = storage_dir
        self.ensure_storage_dir()
    
    def ensure_storage_dir(self):
        """确保存储目录存在"""
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """列出所有知识库"""
        kb_list = []
        
        try:
            if not os.path.exists(self.storage_dir):
                return kb_list
            
            for item in os.listdir(self.storage_dir):
                kb_path = os.path.join(self.storage_dir, item)
                if os.path.isdir(kb_path):
                    kb_info = self.get_knowledge_base_info(item)
                    if kb_info:
                        kb_list.append(kb_info)
            
            # 按修改时间排序
            kb_list.sort(key=lambda x: x.get('modified', 0), reverse=True)
            return kb_list
            
        except Exception as e:
            print(f"列出知识库失败: {e}")
            return []
    
    def get_knowledge_base_info(self, kb_name: str) -> Optional[Dict[str, Any]]:
        """获取知识库信息"""
        try:
            kb_path = os.path.join(self.storage_dir, kb_name)
            if not os.path.exists(kb_path):
                return None
            
            # 基础信息
            stat = os.stat(kb_path)
            info = {
                'name': kb_name,
                'path': kb_path,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'size': self._get_directory_size(kb_path)
            }
            
            # 尝试读取元数据
            metadata_file = os.path.join(kb_path, 'metadata.json')
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        info.update(metadata)
                except:
                    pass
            
            # 统计文档数量
            info['document_count'] = self._count_documents(kb_path)
            
            return info
            
        except Exception as e:
            print(f"获取知识库信息失败 {kb_name}: {e}")
            return None
    
    def create_knowledge_base(self, kb_name: str, description: str = "") -> Dict[str, Any]:
        """创建新的知识库"""
        try:
            # 清理知识库名称
            from src.common.utils import sanitize_filename
            clean_name = sanitize_filename(kb_name)
            
            kb_path = os.path.join(self.storage_dir, clean_name)
            
            # 检查是否已存在
            if os.path.exists(kb_path):
                return {
                    'success': False,
                    'message': f'知识库 "{clean_name}" 已存在',
                    'kb_name': clean_name
                }
            
            # 创建目录
            os.makedirs(kb_path, exist_ok=True)
            
            # 创建元数据
            metadata = {
                'name': clean_name,
                'original_name': kb_name,
                'description': description,
                'created': time.time(),
                'modified': time.time(),
                'document_count': 0,
                'version': '1.0'
            }
            
            metadata_file = os.path.join(kb_path, 'metadata.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            return {
                'success': True,
                'message': f'知识库 "{clean_name}" 创建成功',
                'kb_name': clean_name,
                'path': kb_path
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'创建知识库失败: {str(e)}',
                'kb_name': kb_name
            }
    
    def delete_knowledge_base(self, kb_name: str) -> Dict[str, Any]:
        """删除知识库"""
        try:
            kb_path = os.path.join(self.storage_dir, kb_name)
            
            if not os.path.exists(kb_path):
                return {
                    'success': False,
                    'message': f'知识库 "{kb_name}" 不存在'
                }
            
            # 删除目录及所有内容
            import shutil
            shutil.rmtree(kb_path)
            
            return {
                'success': True,
                'message': f'知识库 "{kb_name}" 删除成功'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'删除知识库失败: {str(e)}'
            }
    
    def exists(self, kb_name: str) -> bool:
        """检查知识库是否存在"""
        kb_path = os.path.join(self.storage_dir, kb_name)
        return os.path.exists(kb_path) and os.path.isdir(kb_path)
    
    def update_metadata(self, kb_name: str, metadata: Dict[str, Any]) -> bool:
        """更新知识库元数据"""
        try:
            kb_path = os.path.join(self.storage_dir, kb_name)
            if not os.path.exists(kb_path):
                return False
            
            metadata_file = os.path.join(kb_path, 'metadata.json')
            
            # 读取现有元数据
            existing_metadata = {}
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        existing_metadata = json.load(f)
                except:
                    pass
            
            # 更新元数据
            existing_metadata.update(metadata)
            existing_metadata['modified'] = time.time()
            
            # 保存元数据
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(existing_metadata, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"更新元数据失败: {e}")
            return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            if not os.path.exists(self.storage_dir):
                return {
                    'total_size': 0,
                    'total_kb_count': 0,
                    'total_document_count': 0
                }
            
            total_size = self._get_directory_size(self.storage_dir)
            kb_list = self.list_knowledge_bases()
            total_documents = sum(kb.get('document_count', 0) for kb in kb_list)
            
            return {
                'total_size': total_size,
                'total_kb_count': len(kb_list),
                'total_document_count': total_documents,
                'storage_dir': self.storage_dir
            }
            
        except Exception as e:
            print(f"获取存储统计失败: {e}")
            return {
                'total_size': 0,
                'total_kb_count': 0,
                'total_document_count': 0
            }
    
    def _get_directory_size(self, directory: str) -> int:
        """获取目录大小"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except (OSError, IOError):
                        continue
        except Exception:
            pass
        return total_size
    
    def _count_documents(self, kb_path: str) -> int:
        """统计知识库中的文档数量"""
        count = 0
        try:
            for root, dirs, files in os.walk(kb_path):
                # 排除元数据文件
                count += len([f for f in files if not f.startswith('.') and f != 'metadata.json'])
        except Exception:
            pass
        return count

# 全局知识库服务实例
_kb_service = None

def get_knowledge_base_service() -> KnowledgeBaseService:
    """获取知识库服务实例"""
    global _kb_service
    if _kb_service is None:
        _kb_service = KnowledgeBaseService()
    return _kb_service
