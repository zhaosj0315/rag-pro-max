"""
增强文档上传处理器
支持多模态文档处理
"""

import os
from typing import List, Dict, Any
from src.processors.multimodal_processor import multimodal_processor
from src.processors.upload_handler import UploadHandler
from src.app_logging import LogManager

logger = LogManager()

class EnhancedUploadHandler(UploadHandler):
    """增强文档上传处理器"""
    
    def __init__(self):
        super().__init__()
        self.multimodal_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.xlsx', '.xls', '.csv']
    
    def process_uploaded_file(self, uploaded_file, temp_dir: str) -> Dict[str, Any]:
        """处理上传的文件（支持多模态）"""
        try:
            # 保存文件
            file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # 检查是否为多模态文件
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            
            if file_ext in self.multimodal_formats:
                # 多模态处理
                result = multimodal_processor.process_document(file_path)
                logger.info(f"📄 多模态文件处理: {uploaded_file.name}")
                
                return {
                    "file_path": file_path,
                    "file_name": uploaded_file.name,
                    "file_size": uploaded_file.size,
                    "multimodal": True,
                    "content": result
                }
            else:
                # 标准文档处理
                return {
                    "file_path": file_path,
                    "file_name": uploaded_file.name,
                    "file_size": uploaded_file.size,
                    "multimodal": False
                }
                
        except Exception as e:
            logger.error(f"文件处理失败: {e}")
            return None
    
    def batch_process_files(self, file_paths: List[str]) -> List[Dict[str, Any]]:
        """批量处理文件"""
        results = []
        
        for file_path in file_paths:
            try:
                file_ext = os.path.splitext(file_path)[1].lower()
                
                if file_ext in self.multimodal_formats:
                    # 多模态处理
                    content = multimodal_processor.process_document(file_path)
                    results.append({
                        "file_path": file_path,
                        "multimodal": True,
                        "content": content
                    })
                else:
                    # 标准处理
                    results.append({
                        "file_path": file_path,
                        "multimodal": False
                    })
                    
            except Exception as e:
                logger.error(f"批量处理失败 {file_path}: {e}")
                continue
        
        return results

# 全局增强上传处理器
enhanced_upload_handler = EnhancedUploadHandler()
