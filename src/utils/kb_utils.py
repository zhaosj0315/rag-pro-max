"""
知识库工具函数 - 从主文件中提取的工具函数
"""

import os
import time
import streamlit as st


def generate_smart_kb_name(target_path, cnt, file_types, folder_name):
    """智能生成知识库名称 - 使用优化器确保唯一性"""
    
    # 策略1：单文件特例处理 - 直接使用文件名作为知识库名称
    if cnt == 1 and os.path.exists(target_path):
        try:
            # 查找目录中的那个唯一文件（忽略隐藏文件）
            files = [f for f in os.listdir(target_path) if not f.startswith('.') and os.path.isfile(os.path.join(target_path, f))]
            if len(files) >= 1:
                single_file = files[0]
                name_without_ext = os.path.splitext(single_file)[0]
                
                from src.utils.document_processor import sanitize_filename
                suggested_name = sanitize_filename(name_without_ext)
                
                # 如果文件名有效，直接使用它
                if suggested_name and len(suggested_name) > 1:
                    from src.utils.kb_name_optimizer import KBNameOptimizer
                    output_base = os.path.join(os.getcwd(), "vector_db_storage")
                    return KBNameOptimizer.generate_unique_name(suggested_name, output_base)
        except Exception:
            pass  # 出错则回退到原有逻辑

    # 使用优化器的建议名称功能
    try:
        from src.utils.kb_name_optimizer import KBNameOptimizer
        suggested_name = KBNameOptimizer.suggest_name_from_content(target_path, cnt, list(file_types.keys()))
    except:
        suggested_name = None
    
    # 如果没有建议名称，使用备用逻辑
    if not suggested_name:
        # 分析文件类型
        main_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
        if not main_types:
            suggested_name = "文档知识库"
        else:
            main_ext = main_types[0][0].replace('.', '').upper()
            
            # 根据文件类型生成基础名称
            type_names = {
                'PDF': 'PDF文档库', 'DOCX': 'Word文档库', 'DOC': 'Word文档库',
                'MD': 'Markdown笔记', 'TXT': '文本文档库',
                'PY': 'Python代码库', 'JS': 'JavaScript代码库', 'JAVA': 'Java代码库',
                'XLSX': 'Excel数据库', 'CSV': 'CSV数据集',
                'PPT': 'PPT演示库', 'PPTX': 'PPT演示库',
                'HTML': '网页文档库', 'JSON': 'JSON配置库'
            }
            
            if len(main_types) == 1:
                suggested_name = type_names.get(main_ext, f"{main_ext}文档库")
            else:
                suggested_name = f"混合文档库_{cnt}个文件"
    
    # 使用优化器确保名称唯一性（会在需要时添加时间戳）
    try:
        from src.utils.kb_name_optimizer import KBNameOptimizer
        output_base = os.path.join(os.getcwd(), "vector_db_storage")
        return KBNameOptimizer.generate_unique_name(suggested_name, output_base)
    except:
        # 降级到简单的时间戳方案
        return f"{suggested_name}_{int(time.time())}"


