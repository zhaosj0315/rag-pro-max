"""
知识库下载服务
提供知识库内容的打包下载功能
"""

import os
import json
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
import streamlit as st

class KnowledgeBaseDownloadService:
    def __init__(self):
        self.storage_dir = "vector_db_storage"
    
    def get_downloadable_items(self, kb_name: str) -> Dict:
        """获取可下载的项目列表"""
        kb_path = Path(self.storage_dir) / kb_name
        if not kb_path.exists():
            return {}
        
        items = {
            'original_files': [],
            'metadata': None,
            'vector_data': None,
            'summaries': None,
            'chat_history': []
        }
        
        # 1. 原始文件 - 检查多个可能的位置
        possible_docs_paths = [
            kb_path / "docs",
            kb_path / "documents", 
            kb_path / "files",
            kb_path / "uploads"
        ]
        
        for docs_path in possible_docs_paths:
            if docs_path.exists():
                for file_path in docs_path.rglob("*"):
                    if file_path.is_file():
                        items['original_files'].append({
                            'name': file_path.name,
                            'path': str(file_path),
                            'size': file_path.stat().st_size
                        })
                break
        
        # 如果没有找到专门的文档目录，检查是否有原始文件的记录
        if not items['original_files']:
            # 检查manifest.json中是否有文件信息
            manifest_path = kb_path / "manifest.json"
            if manifest_path.exists():
                try:
                    import json
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                    
                    files_info = manifest.get('files', [])
                    if files_info:
                        items['original_files'] = []
                        for f in files_info:
                            # 安全处理文件大小
                            size = f.get('size', 0)
                            if isinstance(size, str):
                                try:
                                    # 尝试解析字符串中的数字
                                    import re
                                    size_match = re.search(r'([\d.]+)', str(size))
                                    if size_match:
                                        size = float(size_match.group(1))
                                        # 如果包含单位，进行转换
                                        if 'KB' in str(f.get('size', '')).upper():
                                            size = int(size * 1024)
                                        elif 'MB' in str(f.get('size', '')).upper():
                                            size = int(size * 1024 * 1024)
                                        else:
                                            size = int(size)
                                    else:
                                        size = 0
                                except:
                                    size = 0
                            elif not isinstance(size, (int, float)):
                                size = 0
                            
                            file_info = {
                                'name': f.get('name', '未知文件'),
                                'path': f.get('path', ''),
                                'size': int(size)  # 确保是整数
                            }
                            items['original_files'].append(file_info)
                except:
                    pass
        
        # 2. 元数据文件 - 检查多个可能的文件
        metadata_files = ['.kb_info.json', 'kb_info.json', 'metadata.json', 'manifest.json']
        for meta_file in metadata_files:
            meta_path = kb_path / meta_file
            if meta_path.exists():
                items['metadata'] = str(meta_path)
                break
        
        # 3. 向量数据 - 检查向量存储文件
        vector_files = [
            'default__vector_store.json', 
            'image__vector_store.json',
            'index_store.json', 
            'docstore.json',
            'graph_store.json'
        ]
        for vec_file in vector_files:
            vec_path = kb_path / vec_file
            if vec_path.exists():
                items['vector_data'] = str(kb_path)
                break
        
        # 4. 摘要文件
        summary_paths = [
            kb_path / "summaries",
            kb_path / "summary", 
            kb_path / "abstracts"
        ]
        for summary_path in summary_paths:
            if summary_path.exists():
                items['summaries'] = str(summary_path)
                break
        
        # 5. 聊天历史
        chat_dir = Path("chat_histories")
        if chat_dir.exists():
            chat_files = list(chat_dir.glob(f"*{kb_name}*"))
            if chat_files:
                items['chat_history'] = [str(f) for f in chat_files if f.is_file()]
        
        return items
    
    def create_download_package(self, kb_name: str, selected_items: List[str]) -> Optional[str]:
        """创建下载包"""
        try:
            kb_path = Path(self.storage_dir) / kb_name
            if not kb_path.exists():
                return None
            
            # 创建临时zip文件
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, f"{kb_name}_export.zip")
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                
                # 添加原始文件
                if 'original_files' in selected_items:
                    files_added = False
                    
                    # 方法1: 先尝试从文档目录复制
                    docs_paths = [kb_path / "docs", kb_path / "documents", kb_path / "files", kb_path / "uploads"]
                    for docs_path in docs_paths:
                        if docs_path.exists():
                            for file_path in docs_path.rglob("*"):
                                if file_path.is_file():
                                    arcname = f"original_files/{file_path.relative_to(docs_path)}"
                                    zipf.write(file_path, arcname)
                                    files_added = True
                            if files_added:
                                break
                    
                    # 方法2: 如果没有找到文档目录，尝试从manifest.json获取文件信息
                    if not files_added:
                        manifest_path = kb_path / "manifest.json"
                        if manifest_path.exists():
                            try:
                                import json
                                with open(manifest_path, 'r', encoding='utf-8') as f:
                                    manifest = json.load(f)
                                
                                files_info = manifest.get('files', [])
                                for file_info in files_info:
                                    file_path = file_info.get('path', '')
                                    file_name = file_info.get('name', '')
                                    
                                    # 如果路径有效，直接使用
                                    if file_path and file_path != '未知' and os.path.exists(file_path):
                                        arcname = f"original_files/{file_name}"
                                        zipf.write(file_path, arcname)
                                        files_added = True
                                    # 如果路径无效，尝试在常见位置查找文件
                                    elif file_name:
                                        search_paths = [
                                            f"temp_uploads/batch_*/{file_name}",  # 批量上传目录
                                            f"temp_uploads/{file_name}",
                                            f"uploads/{file_name}",
                                            f"data/{file_name}",
                                            file_name  # 当前目录
                                        ]
                                        
                                        # 对于包含通配符的路径，使用glob搜索
                                        import glob
                                        for search_pattern in search_paths:
                                            if '*' in search_pattern:
                                                matches = glob.glob(search_pattern)
                                                if matches:
                                                    # 使用最新的文件
                                                    latest_file = max(matches, key=os.path.getmtime)
                                                    arcname = f"original_files/{file_name}"
                                                    zipf.write(latest_file, arcname)
                                                    files_added = True
                                                    break
                                            else:
                                                if os.path.exists(search_pattern):
                                                    arcname = f"original_files/{file_name}"
                                                    zipf.write(search_pattern, arcname)
                                                    files_added = True
                                                    break
                                        
                                        if files_added:
                                            break
                                
                            except Exception as e:
                                pass
                    
                    # 方法3: 如果仍然没有找到文件，添加说明
                    if not files_added:
                        zipf.writestr("original_files/README.txt", 
                                    "原始文件未找到。\n\n可能的原因:\n1. 文件已被移动或删除\n2. 文件路径信息丢失\n3. 知识库是通过其他方式创建的\n\n建议检查知识库的创建方式和文件存储位置。")
                
                # 添加元数据
                if 'metadata' in selected_items:
                    metadata_files = ['.kb_info.json', 'kb_info.json', 'metadata.json', 'manifest.json']
                    for meta_file in metadata_files:
                        meta_path = kb_path / meta_file
                        if meta_path.exists():
                            zipf.write(meta_path, f"metadata/{meta_file}")
                
                # 添加向量数据
                if 'vector_data' in selected_items:
                    vector_files = [
                        'default__vector_store.json', 
                        'image__vector_store.json',
                        'index_store.json', 
                        'docstore.json',
                        'graph_store.json'
                    ]
                    for vec_file in vector_files:
                        vec_path = kb_path / vec_file
                        if vec_path.exists():
                            zipf.write(vec_path, f"vector_data/{vec_file}")
                
                # 添加摘要
                if 'summaries' in selected_items:
                    summary_path = kb_path / "summaries"
                    if summary_path.exists():
                        for file_path in summary_path.rglob("*"):
                            if file_path.is_file():
                                arcname = f"summaries/{file_path.relative_to(summary_path)}"
                                zipf.write(file_path, arcname)
                
                # 添加聊天历史
                if 'chat_history' in selected_items:
                    chat_dir = Path("chat_histories")
                    if chat_dir.exists():
                        chat_files = list(chat_dir.glob(f"*{kb_name}*"))
                        for chat_file in chat_files:
                            if chat_file.is_file():
                                arcname = f"chat_history/{chat_file.name}"
                                zipf.write(chat_file, arcname)
                
                # 添加说明文件
                readme_content = self._generate_readme(kb_name, selected_items)
                zipf.writestr("README.txt", readme_content)
            
            return zip_path
            
        except Exception as e:
            st.error(f"创建下载包失败: {e}")
            return None
    
    def _generate_readme(self, kb_name: str, selected_items: List[str]) -> str:
        """生成说明文件"""
        content = f"""RAG Pro Max 知识库导出包
=========================

知识库名称: {kb_name}
导出时间: {st.session_state.get('current_time', '未知')}
导出内容:
"""
        
        if 'original_files' in selected_items:
            content += "- original_files/: 原始上传文件\n"
        if 'metadata' in selected_items:
            content += "- metadata/: 知识库元数据信息\n"
        if 'vector_data' in selected_items:
            content += "- vector_data/: 向量化数据和索引\n"
        if 'summaries' in selected_items:
            content += "- summaries/: 文档摘要信息\n"
        if 'chat_history' in selected_items:
            content += "- chat_history/: 聊天对话记录\n"
        
        content += """
使用说明:
1. original_files/ 包含您上传的原始文件
2. metadata/ 包含知识库的配置和描述信息
3. vector_data/ 包含向量化后的数据，可用于重建知识库
4. summaries/ 包含自动生成的文档摘要
5. chat_history/ 包含与该知识库的所有对话记录

注意: 向量数据需要相同的嵌入模型才能正确使用
"""
        return content

# 全局服务实例
_download_service = None

def get_download_service() -> KnowledgeBaseDownloadService:
    """获取下载服务实例"""
    global _download_service
    if _download_service is None:
        _download_service = KnowledgeBaseDownloadService()
    return _download_service
