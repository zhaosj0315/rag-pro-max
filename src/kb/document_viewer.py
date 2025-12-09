"""
文档查看器模块 - Document Viewer
支持文档预览、查看、编辑、删除
"""

import os
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path


class DocumentInfo:
    """文档信息"""
    
    def __init__(self, file_path: str, kb_name: str):
        self.file_path = file_path
        self.kb_name = kb_name
        self.name = os.path.basename(file_path)
        self.size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        self.upload_time = datetime.fromtimestamp(
            os.path.getctime(file_path)
        ).strftime("%Y-%m-%d %H:%M:%S") if os.path.exists(file_path) else "未知"
    
    @property
    def size_mb(self) -> float:
        """文件大小（MB）"""
        return self.size / (1024 * 1024)
    
    @property
    def extension(self) -> str:
        """文件扩展名"""
        return os.path.splitext(self.name)[1].lower()


class DocumentViewer:
    """文档查看器"""
    
    def __init__(self, vector_db_path: str = "vector_db_storage"):
        self.vector_db_path = vector_db_path
    
    def get_kb_documents(self, kb_name: str) -> List[DocumentInfo]:
        """
        获取知识库的所有文档
        
        Args:
            kb_name: 知识库名称
            
        Returns:
            文档信息列表
        """
        kb_path = os.path.join(self.vector_db_path, kb_name)
        if not os.path.exists(kb_path):
            return []
        
        # 从 manifest.json 读取文档列表
        manifest_path = os.path.join(kb_path, "manifest.json")
        if os.path.exists(manifest_path):
            import json
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    files = manifest.get('files', [])
                    docs = []
                    
                    for f in files:
                        if isinstance(f, dict):
                            # 从字典中获取文件名
                            file_name = f.get('name', '')
                            if not file_name:
                                continue
                            
                            # 构建完整路径
                            # 文件通常在 temp_uploads/kb_name/ 目录下
                            possible_paths = [
                                os.path.join('temp_uploads', kb_name, file_name),  # 最常见
                                file_name,  # 绝对路径
                                os.path.join('temp_uploads', file_name),  # temp_uploads根目录
                                os.path.join(kb_path, file_name),  # 知识库目录
                            ]
                            
                            file_path = None
                            for path in possible_paths:
                                if os.path.exists(path):
                                    file_path = path
                                    break
                            
                            if file_path:
                                # 创建一个临时的 DocumentInfo，使用 manifest 中的信息
                                doc = DocumentInfo.__new__(DocumentInfo)
                                doc.file_path = file_path
                                doc.kb_name = kb_name
                                doc.name = file_name
                                doc.size = f.get('size_bytes', 0)
                                doc.upload_time = f.get('added_at', '未知')
                                docs.append(doc)
                        else:
                            # 兼容旧格式（字符串路径）
                            file_path = f
                            if file_path and os.path.exists(file_path):
                                docs.append(DocumentInfo(file_path, kb_name))
                    
                    return docs
            except Exception as e:
                print(f"读取 manifest 失败: {e}")
        
        return []
    
    def preview_file(self, file_path: str, max_chars: int = 1000) -> str:
        """
        预览文件内容
        
        Args:
            file_path: 文件路径
            max_chars: 最大字符数
            
        Returns:
            预览内容
        """
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            # 文本文件直接读取
            if ext in ['.txt', '.md', '.json', '.csv']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(max_chars)
                    if len(content) == max_chars:
                        content += "\n\n... (内容过长，已截断)"
                    return content
            
            # PDF 文件
            elif ext == '.pdf':
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in reader.pages[:3]:  # 只读前3页
                            text += page.extract_text() + "\n"
                        if len(text) > max_chars:
                            text = text[:max_chars] + "\n\n... (内容过长，已截断)"
                        return text
                except:
                    return "PDF 预览失败（可能需要 OCR）"
            
            # DOCX 文件
            elif ext == '.docx':
                try:
                    from docx import Document
                    doc = Document(file_path)
                    text = "\n".join([p.text for p in doc.paragraphs[:10]])
                    if len(text) > max_chars:
                        text = text[:max_chars] + "\n\n... (内容过长，已截断)"
                    return text
                except:
                    return "DOCX 预览失败"
            
            else:
                return f"不支持预览 {ext} 格式"
                
        except Exception as e:
            return f"预览失败: {str(e)}"
    
    def get_document_chunks(self, kb_name: str, file_path: str, max_chunks: int = 10) -> List[Dict]:
        """
        获取文档的分块信息
        
        Args:
            kb_name: 知识库名称
            file_path: 文件路径
            max_chunks: 最大分块数
            
        Returns:
            分块列表
        """
        try:
            from llama_index.core import StorageContext, load_index_from_storage
            
            kb_path = os.path.join(self.vector_db_path, kb_name)
            storage_context = StorageContext.from_defaults(persist_dir=kb_path)
            index = load_index_from_storage(storage_context)
            
            # 获取所有节点
            docstore = storage_context.docstore
            nodes = list(docstore.docs.values())
            
            # 筛选属于该文件的节点
            file_name = os.path.basename(file_path)
            file_nodes = [
                node for node in nodes 
                if node.metadata.get('file_name') == file_name or 
                   node.metadata.get('file_path') == file_path
            ]
            
            # 转换为字典格式
            chunks = []
            for i, node in enumerate(file_nodes[:max_chunks]):
                chunks.append({
                    'index': i + 1,
                    'text': node.get_content(),
                    'metadata': node.metadata
                })
            
            return chunks
            
        except Exception as e:
            print(f"获取文档分块失败: {e}")
            return []
    
    def delete_document(self, kb_name: str, file_path: str) -> bool:
        """
        删除文档（从知识库中移除）
        
        Args:
            kb_name: 知识库名称
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        try:
            # 更新 manifest
            manifest_path = os.path.join(self.vector_db_path, kb_name, "manifest.json")
            if os.path.exists(manifest_path):
                import json
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                
                files = manifest.get('files', [])
                if file_path in files:
                    files.remove(file_path)
                    manifest['files'] = files
                    
                    with open(manifest_path, 'w', encoding='utf-8') as f:
                        json.dump(manifest, f, ensure_ascii=False, indent=2)
            
            # 注意：这里只是从 manifest 移除，实际的向量数据需要重建索引才能删除
            # 完整实现需要支持增量更新
            return True
            
        except Exception as e:
            print(f"删除文档失败: {e}")
            return False
