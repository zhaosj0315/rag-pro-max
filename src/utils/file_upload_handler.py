import os
import tempfile
from typing import Optional, Tuple
from src.file_processor import _load_single_file

def process_uploaded_file_content(uploaded_file) -> Tuple[Optional[str], Optional[str]]:
    """
    处理 Streamlit 上传的文件，复用 src/file_processor.py 的核心逻辑。
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        
    Returns:
        (text_content, error_message)
    """
    if not uploaded_file:
        return None, "未选择文件"

    try:
        # 获取文件扩展名
        file_name = uploaded_file.name
        file_ext = "." + file_name.split('.')[-1].lower() if '.' in file_name else ""
        
        # 创建临时文件保存上传内容，因为 _load_single_file 需要文件路径
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
            
        try:
            # 构造 file_info 元组: (path, filename, extension)
            file_info = (tmp_path, file_name, file_ext)
            
            # 调用核心处理逻辑，默认启用 OCR
            # _load_single_file 返回: (docs, file_name, status, info, read_mode)
            # 或者在错误时返回: (None, file_name, 'failed', error_msg, read_mode)
            result = _load_single_file(file_info, use_ocr=True)
            
            # 解析返回结果
            if result and len(result) >= 3:
                docs = result[0]
                status = result[2]
                
                if status == 'success' and docs:
                    # 合并所有文档的文本
                    full_text = "\n\n".join([d.text for d in docs if d.text])
                    return full_text, None
                elif status == 'failed':
                    error_msg = result[3] if len(result) > 3 else "未知错误"
                    return None, f"解析失败: {error_msg}"
                elif status == 'skipped':
                    reason = result[3] if len(result) > 3 else "被跳过"
                    return None, f"文件被跳过: {reason}"
            
            return None, "未知处理结果"
            
        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        return None, f"处理异常: {str(e)}"
