"""
文档上传处理器
Stage 4.1 - 提取自 apppro.py
"""

import os
import time
import zipfile
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class UploadResult:
    """上传结果"""
    success_count: int
    skipped_count: int
    skip_reasons: List[str]
    batch_dir: str


class UploadHandler:
    """文档上传处理器"""
    
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_ZIP_SIZE = 500 * 1024 * 1024   # 500MB
    ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.docx', '.md', '.xlsx', '.csv', 
                         '.pptx', '.html', '.json', '.zip'}
    
    def __init__(self, upload_dir: str, logger=None):
        self.upload_dir = upload_dir
        self.logger = logger
    
    def process_uploads(self, uploaded_files) -> UploadResult:
        """处理上传的文件"""
        batch_dir = os.path.join(self.upload_dir, f"batch_{int(time.time())}")
        os.makedirs(batch_dir, exist_ok=True)
        
        success_count = 0
        skipped_count = 0
        skip_reasons = []
        
        for f in uploaded_files:
            try:
                # 验证文件
                if not self._validate_file(f, skip_reasons):
                    skipped_count += 1
                    continue
                
                # 保存文件
                file_path = os.path.join(batch_dir, f.name)
                with open(file_path, "wb") as w:
                    w.write(f.getbuffer())
                
                # 处理 ZIP
                if f.name.endswith('.zip'):
                    if not self._extract_zip(file_path, batch_dir, f.name, skip_reasons):
                        skipped_count += 1
                        continue
                
                if self.logger:
                    self.logger.log_file_upload(f.name, "success")
                success_count += 1
                
            except Exception as e:
                if self.logger:
                    self.logger.log_file_upload(f.name, "error", str(e))
                skipped_count += 1
                skip_reasons.append(f"{f.name}: 系统错误")
        
        return UploadResult(success_count, skipped_count, skip_reasons, batch_dir)
    
    def _validate_file(self, file, skip_reasons: List[str]) -> bool:
        """验证文件大小和类型"""
        # 检查大小
        if file.size > self.MAX_FILE_SIZE:
            skip_reasons.append(f"{file.name}: 超过100MB")
            return False
        
        # 检查扩展名
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            skip_reasons.append(f"{file.name}: 类型不支持 ({ext})")
            return False
        
        return True
    
    def _extract_zip(self, zip_path: str, extract_dir: str, 
                     filename: str, skip_reasons: List[str]) -> bool:
        """解压 ZIP 文件（带安全检查）"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                # ZIP炸弹检查
                total_size = sum(info.file_size for info in z.infolist())
                if total_size > self.MAX_ZIP_SIZE:
                    skip_reasons.append(f"{filename}: ZIP解压后过大(>500MB)")
                    os.remove(zip_path)
                    return False
                
                # 路径遍历检查
                for info in z.infolist():
                    if info.filename.startswith('/') or '..' in info.filename:
                        skip_reasons.append(f"{filename}: ZIP包含非法路径")
                        os.remove(zip_path)
                        return False
                
                z.extractall(extract_dir)
            os.remove(zip_path)
            return True
            
        except Exception as e:
            skip_reasons.append(f"{filename}: ZIP解压失败 {str(e)}")
            if os.path.exists(zip_path):
                os.remove(zip_path)
            return False
    
    @staticmethod
    def get_folder_stats(path: str) -> Tuple[int, dict, int]:
        """获取文件夹统计信息"""
        all_files = []
        file_types = {}
        total_size = 0
        
        for root, _, files in os.walk(path):
            for f in files:
                if not f.startswith('.'):
                    all_files.append(f)
                    ext = os.path.splitext(f)[1].upper() or 'OTHER'
                    file_types[ext] = file_types.get(ext, 0) + 1
                    try:
                        total_size += os.path.getsize(os.path.join(root, f))
                    except:
                        pass
        
        return len(all_files), file_types, total_size
