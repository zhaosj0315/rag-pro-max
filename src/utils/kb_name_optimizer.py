"""知识库名称优化器 - 统一的智能命名与查重系统"""

import os
import re
import time
from datetime import datetime
from urllib.parse import urlparse
from src.common.utils import sanitize_filename


class KBNameOptimizer:
    """知识库名称优化器"""
    
    @staticmethod
    def smart_generate(staging_path: str, source_type: str = "auto", source_info: str = "") -> str:
        """
        统一的智能知识库命名入口 - 根据暂存区材料生成有意义的名称
        
        Args:
            staging_path: 暂存区路径
            source_type: 来源类型 ("auto", "file", "url", "search", "database")
            source_info: 额外信息 (URL、关键词、数据库名等)
            
        Returns:
            带时间戳的唯一知识库名称
        """
        output_base = os.path.join(os.getcwd(), "vector_db_storage")
        
        # 分析暂存区内容
        file_count, file_types = KBNameOptimizer._analyze_staging_content(staging_path)
        
        # 自动检测来源类型
        if source_type == "auto":
            source_type = KBNameOptimizer._detect_source_type(staging_path, file_count, file_types)
        
        # 根据来源类型生成基础名称
        if source_type == "url" and source_info:
            base_name = KBNameOptimizer._generate_url_base_name(source_info)
        elif source_type == "search" and source_info:
            base_name = KBNameOptimizer._generate_search_base_name(source_info)
        elif source_type == "database" and source_info:
            base_name = KBNameOptimizer._generate_database_base_name(source_info)
        else:
            # 文件类型，根据暂存区内容智能生成
            base_name = KBNameOptimizer._generate_content_base_name(staging_path, file_count, file_types, source_type)
        
        # 生成带时间戳的唯一名称
        return KBNameOptimizer._generate_timestamped_unique_name(base_name, output_base)
    
    @staticmethod
    def _detect_source_type(staging_path: str, file_count: int, file_types: dict) -> str:
        """自动检测来源类型"""
        if not os.path.exists(staging_path):
            return "file"
        
        # 检查文件名模式来推断来源
        for root, dirs, files in os.walk(staging_path):
            for file in files:
                if file.startswith('.') or file.endswith('.meta'):
                    continue
                
                # 数据库快照文件模式: [DB]Alias_DB_Source_Time.csv
                if file.startswith('[DB]') and file.endswith('.csv'):
                    return "database"
                # 自定义SQL文件模式: [SQL]...
                elif file.startswith('[SQL]') and file.endswith('.csv'):
                    return "database"
                # 网页文件模式: Web_...
                elif file.startswith('Web_'):
                    return "url"
                # 搜索文件模式: Search_...
                elif file.startswith('Search_'):
                    return "search"
                # 粘贴文本模式: Pasted_...
                elif file.startswith('Pasted_'):
                    return "paste"
        
        return "file"
    
    @staticmethod
    def _analyze_staging_content(staging_path: str) -> tuple:
        """分析暂存区内容，返回文件数量和类型统计"""
        if not os.path.exists(staging_path):
            return 0, {}
        
        file_types = {}
        file_count = 0
        
        for root, dirs, files in os.walk(staging_path):
            for file in files:
                if file.startswith('.') or file.endswith('.meta'):
                    continue  # 跳过隐藏文件和审计文件
                
                file_count += 1
                ext = os.path.splitext(file)[1].lower()
                file_types[ext] = file_types.get(ext, 0) + 1
        
        return file_count, file_types
    
    @staticmethod
    def _generate_content_base_name(staging_path: str, file_count: int, file_types: dict, source_type: str = "file") -> str:
        """根据文件内容和来源类型生成基础名称"""
        if file_count == 0:
            return "空知识库"
        
        # 根据来源类型特殊处理
        if source_type == "database":
            return KBNameOptimizer._generate_database_name_from_files(staging_path)
        elif source_type == "url":
            return KBNameOptimizer._generate_web_name_from_files(staging_path)
        elif source_type == "search":
            return KBNameOptimizer._generate_search_name_from_files(staging_path)
        elif source_type == "paste":
            return "文本粘贴库"
        
        # 文件类型处理
        # 单文件特殊处理
        if file_count == 1:
            try:
                for root, dirs, files in os.walk(staging_path):
                    for file in files:
                        if not file.startswith('.') and not file.endswith('.meta'):
                            name_without_ext = os.path.splitext(file)[0]
                            clean_name = sanitize_filename(name_without_ext)
                            if clean_name and len(clean_name) > 1:
                                return clean_name
            except:
                pass
        
        # 多文件根据类型生成名称
        if not file_types:
            return f"文档库_{file_count}个文件"
        
        # 按文件数量排序，取主要类型
        main_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
        main_ext = main_types[0][0].replace('.', '').upper()
        
        # 类型映射表
        type_names = {
            'PDF': 'PDF文档库', 'DOCX': 'Word文档库', 'DOC': 'Word文档库',
            'MD': 'Markdown笔记库', 'TXT': '文本文档库',
            'PY': 'Python代码库', 'JS': 'JavaScript代码库', 'JAVA': 'Java代码库',
            'XLSX': 'Excel数据库', 'CSV': 'CSV数据集', 'XLS': 'Excel数据库',
            'PPT': 'PPT演示库', 'PPTX': 'PPT演示库',
            'HTML': '网页文档库', 'JSON': 'JSON配置库',
            'XML': 'XML文档库', 'YAML': 'YAML配置库', 'YML': 'YAML配置库'
        }
        
        if len(main_types) == 1:
            return type_names.get(main_ext, f"{main_ext}文档库")
        else:
            return f"混合文档库_{file_count}个文件"
    
    @staticmethod
    def _generate_database_name_from_files(staging_path: str) -> str:
        """从数据库文件名中提取信息生成名称"""
        try:
            for root, dirs, files in os.walk(staging_path):
                for file in files:
                    if file.startswith('[DB]') and file.endswith('.csv'):
                        # 格式: [DB]Alias_DB_Source_Time.csv
                        name_part = file[4:-4]  # 去掉 [DB] 和 .csv
                        parts = name_part.split('_')
                        if len(parts) >= 2:
                            alias = parts[0]
                            db_name = parts[1]
                            return f"DB_{alias}_{db_name}"
                        else:
                            return f"DB_{parts[0]}"
                    elif file.startswith('[SQL]') and file.endswith('.csv'):
                        return "自定义SQL查询"
        except:
            pass
        return "数据库快照"
    
    @staticmethod
    def _generate_web_name_from_files(staging_path: str) -> str:
        """从网页文件名中提取信息生成名称"""
        try:
            for root, dirs, files in os.walk(staging_path):
                for file in files:
                    if file.startswith('Web_'):
                        # 提取域名部分
                        name_part = file[4:]  # 去掉 Web_
                        if '_' in name_part:
                            domain = name_part.split('_')[0]
                            return f"Web_{domain}"
                        else:
                            return "Web_页面"
        except:
            pass
        return "网页内容"
    
    @staticmethod
    def _generate_search_name_from_files(staging_path: str) -> str:
        """从搜索文件名中提取信息生成名称"""
        try:
            for root, dirs, files in os.walk(staging_path):
                for file in files:
                    if file.startswith('Search_'):
                        # 提取关键词部分
                        name_part = file[7:]  # 去掉 Search_
                        if '_' in name_part:
                            keyword = name_part.split('_')[0]
                            return f"Search_{keyword}"
                        else:
                            return "搜索结果"
        except:
            pass
        return "搜索内容"
    
    @staticmethod
    def _generate_url_base_name(url: str) -> str:
        """根据URL生成基础名称"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '')
            
            # 提取域名核心部分
            parts = domain.split('.')
            if len(parts) >= 2:
                core = parts[0]  # 取主域名部分，如 google.com -> google
            else:
                core = domain.replace('.', '_').replace('-', '_')
            
            return f"Web_{core}"
        except:
            return "Web_页面"
    
    @staticmethod
    def _generate_search_base_name(keyword: str) -> str:
        """根据搜索关键词生成基础名称"""
        safe_keyword = sanitize_filename(keyword).replace(' ', '_')
        if len(safe_keyword) > 20:
            safe_keyword = safe_keyword[:20]
        return f"Search_{safe_keyword}"
    
    @staticmethod
    def _generate_database_base_name(db_info: str) -> str:
        """根据数据库信息生成基础名称"""
        # db_info 格式可能是 "alias_database" 或 "database"
        parts = db_info.split('_')
        if len(parts) >= 2:
            return f"DB_{parts[0]}_{parts[1]}"
        else:
            return f"DB_{db_info}"
    
    @staticmethod
    def _generate_timestamped_unique_name(base_name: str, output_base: str) -> str:
        """生成带时间戳的唯一名称，确保不重复"""
        if not base_name:
            base_name = "知识库"
        
        # 清理基础名称中已有的时间戳
        clean_name = KBNameOptimizer._clean_existing_timestamp(base_name)
        
        # 生成时间戳（年月日+时分秒）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        timestamped_name = f"{clean_name}_{timestamp}"
        
        # 检查是否存在冲突（极少情况）
        if KBNameOptimizer._name_exists(timestamped_name, output_base):
            counter = 1
            while True:
                candidate = f"{timestamped_name}_{counter}"
                if not KBNameOptimizer._name_exists(candidate, output_base):
                    return candidate
                counter += 1
        
        return timestamped_name
    
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
