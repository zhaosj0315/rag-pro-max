"""
批量操作工具 - 文件夹拖拽和批量管理
"""

import os
import shutil
import streamlit as st
from pathlib import Path
from typing import List, Dict

class BatchOperations:
    def __init__(self):
        self.supported_extensions = {'.pdf', '.txt', '.docx', '.md', '.xlsx', '.pptx', '.csv', '.html', '.json'}
    
    def scan_folder(self, folder_path: str) -> Dict:
        """扫描文件夹，返回支持的文件列表"""
        folder_path = Path(folder_path)
        if not folder_path.exists():
            return {'files': [], 'total': 0, 'supported': 0, 'unsupported': 0}
        
        all_files = []
        supported_files = []
        
        # 递归扫描文件夹
        for file_path in folder_path.rglob('*'):
            if file_path.is_file():
                all_files.append(file_path)
                if file_path.suffix.lower() in self.supported_extensions:
                    supported_files.append({
                        'path': str(file_path),
                        'name': file_path.name,
                        'size': file_path.stat().st_size,
                        'type': file_path.suffix.lower(),
                        'relative_path': str(file_path.relative_to(folder_path))
                    })
        
        return {
            'files': supported_files,
            'total': len(all_files),
            'supported': len(supported_files),
            'unsupported': len(all_files) - len(supported_files)
        }
    
    def batch_copy_files(self, files: List[Dict], target_dir: str) -> Dict:
        """批量复制文件到目标目录"""
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        failed_files = []
        
        for file_info in files:
            try:
                source_path = Path(file_info['path'])
                # 保持相对路径结构
                relative_path = file_info['relative_path']
                target_file = target_path / relative_path
                
                # 创建目标目录
                target_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 复制文件
                shutil.copy2(source_path, target_file)
                success_count += 1
                
            except Exception as e:
                failed_files.append({
                    'file': file_info['name'],
                    'error': str(e)
                })
        
        return {
            'success_count': success_count,
            'failed_count': len(failed_files),
            'failed_files': failed_files
        }
    
    def batch_delete_files(self, file_paths: List[str]) -> Dict:
        """批量删除文件"""
        success_count = 0
        failed_files = []
        
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    success_count += 1
            except Exception as e:
                failed_files.append({
                    'file': os.path.basename(file_path),
                    'error': str(e)
                })
        
        return {
            'success_count': success_count,
            'failed_count': len(failed_files),
            'failed_files': failed_files
        }
    
    def get_file_stats(self, files: List[Dict]) -> Dict:
        """获取文件统计信息"""
        if not files:
            return {'total_size': 0, 'avg_size': 0, 'types': {}}
        
        total_size = sum(f['size'] for f in files)
        types = {}
        
        for file_info in files:
            file_type = file_info['type']
            if file_type not in types:
                types[file_type] = {'count': 0, 'size': 0}
            types[file_type]['count'] += 1
            types[file_type]['size'] += file_info['size']
        
        return {
            'total_size': total_size,
            'avg_size': total_size / len(files),
            'types': types
        }

# 全局批量操作实例
batch_ops = BatchOperations()
