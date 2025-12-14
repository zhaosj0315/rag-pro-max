"""知识库名称优化器 - 避免重复名称和时间戳冲突"""

import os
import re
from datetime import datetime
from typing import Optional


class KBNameOptimizer:
    """知识库名称优化器"""
    
    @staticmethod
    def generate_unique_name(base_name: str, output_base: str) -> str:
        """
        生成唯一的知识库名称，默认添加时间戳
        
        Args:
            base_name: 基础名称
            output_base: 知识库存储目录
            
        Returns:
            带时间戳的唯一名称
        """
        if not base_name:
            base_name = "知识库"
        
        # 清理基础名称，移除已有的时间戳
        clean_name = KBNameOptimizer._clean_existing_timestamp(base_name)
        
        # 默认添加时间戳
        timestamp = datetime.now().strftime('%Y%m%d')
        timestamped_name = f"{clean_name}_{timestamp}"
        
        # 如果带时间戳的名称仍然冲突，添加序号
        if KBNameOptimizer._name_exists(timestamped_name, output_base):
            counter = 1
            while True:
                candidate = f"{timestamped_name}_{counter}"
                if not KBNameOptimizer._name_exists(candidate, output_base):
                    return candidate
                counter += 1
        
        return timestamped_name
    
    @staticmethod
    def _clean_existing_timestamp(name: str) -> str:
        """移除名称中已有的时间戳"""
        # 匹配模式：名称_20241214_143059 或 名称_20241214
        patterns = [
            r'_\d{8}_\d{6}$',  # _20241214_143059
            r'_\d{8}$',        # _20241214
            r'_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}$',  # _2024-12-14_14-30-59
            r'_\d{4}-\d{2}-\d{2}$'  # _2024-12-14
        ]
        
        clean_name = name
        for pattern in patterns:
            clean_name = re.sub(pattern, '', clean_name)
        
        return clean_name.strip()
    
    @staticmethod
    def _name_exists(name: str, output_base: str) -> bool:
        """检查知识库名称是否已存在"""
        kb_path = os.path.join(output_base, name)
        return os.path.exists(kb_path)
    
    @staticmethod
    def _generate_timestamped_name(base_name: str, output_base: str) -> str:
        """生成带时间戳的唯一名称"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        timestamped_name = f"{base_name}_{timestamp}"
        
        # 如果带时间戳的名称仍然冲突（极少情况），添加序号
        if KBNameOptimizer._name_exists(timestamped_name, output_base):
            counter = 1
            while True:
                candidate = f"{timestamped_name}_{counter}"
                if not KBNameOptimizer._name_exists(candidate, output_base):
                    return candidate
                counter += 1
        
        return timestamped_name
    
    @staticmethod
    def suggest_name_from_content(content_path: str, file_count: int, file_types: list) -> str:
        """根据内容智能建议知识库名称"""
        if not content_path or not os.path.exists(content_path):
            return ""
        
        # 获取文件夹名称作为基础
        folder_name = os.path.basename(content_path)
        
        # 清理文件夹名称
        if folder_name.startswith('batch_'):
            # 如果是批量上传的临时文件夹，尝试从文件类型生成名称
            if file_types:
                main_type = file_types[0] if len(file_types) == 1 else "混合文档"
                return f"{main_type}知识库"
            else:
                return "文档知识库"
        
        # 移除已有时间戳
        clean_folder_name = KBNameOptimizer._clean_existing_timestamp(folder_name)
        
        # 如果清理后名称为空或太短，使用默认名称
        if not clean_folder_name or len(clean_folder_name) < 2:
            return f"知识库_{file_count}个文件"
        
        return clean_folder_name

    @staticmethod
    def generate_name_from_url(url: str, output_base: str) -> str:
        """
        根据URL生成知识库名称
        逻辑：提取域名核心部分（去除www/http），前缀Web_
        """
        from urllib.parse import urlparse
        
        try:
            # 简单修复URL以便解析
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            parsed = urlparse(url)
            # 获取域名并清理
            domain = parsed.netloc
            domain = domain.replace('www.', '').replace('.', '_').replace('-', '_')
            
            # 如果是IP地址或很短，保留原样，否则只取第一段（如 google_com -> google）
            # 但用户要求比较完整，保留完整域名结构更好，或者只取核心
            # 用户要求："去除HTTP 3 wcom的那种中间的那个域名" -> google
            parts = domain.split('_')
            if len(parts) > 1 and parts[-1] in ['com', 'org', 'net', 'cn', 'io']:
                domain_core = "_".join(parts[:-1]) # google_com -> google
            else:
                domain_core = domain
                
            base_name = f"Web_{domain_core}"
            return KBNameOptimizer.generate_unique_name(base_name, output_base)
        except:
            return KBNameOptimizer.generate_unique_name("Web_Page", output_base)

    @staticmethod
    def generate_name_from_keyword(keyword: str, output_base: str) -> str:
        """
        根据搜索关键词生成知识库名称
        逻辑：保留关键词，前缀Search_
        """
        # 清理关键词，替换空格为下划线，限制长度
        safe_keyword = sanitize_filename(keyword).replace(' ', '_')
        # 增加长度限制到30，确保"Vision Pro"等不被截断
        if len(safe_keyword) > 30:
            safe_keyword = safe_keyword[:30]
            
        base_name = f"Search_{safe_keyword}"
        return KBNameOptimizer.generate_unique_name(base_name, output_base)


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除非法字符"""
    if not filename:
        return ""
    
    # 移除或替换非法字符
    illegal_chars = r'[<>:"/\\|?*]'
    clean_name = re.sub(illegal_chars, '_', filename)
    
    # 移除首尾空格和点
    clean_name = clean_name.strip(' .')
    
    # 限制长度
    if len(clean_name) > 100:
        clean_name = clean_name[:100]
    
    return clean_name
