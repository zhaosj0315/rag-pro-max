#!/usr/bin/env python3
from src.app_logging.log_manager import LogManager

logger = LogManager()

"""
智能目录选择工具
提供统一的目录选择逻辑，优先选择有文件的目录
"""

import os
import sys
import glob
from typing import List, Tuple, Optional

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from src.logger import logger as base_logger
    # 使用logger的log方法
    class LoggerWrapper:
        def info(self, msg): 
            try:
                base_logger.log(msg)
            except:
                logger.info(f"ℹ️ {msg}")
        def warning(self, msg): 
            try:
                base_logger.log(msg)
            except:
                logger.warning(msg)
    logger = LoggerWrapper()
except ImportError:
    # 如果无法导入logger，使用简单的print
    class SimpleLogger:
        def info(self, msg): logger.info(f"ℹ️ {msg}")
        def warning(self, msg): logger.warning(msg)
    logger = SimpleLogger()

class DirectorySelector:
    """智能目录选择器"""
    
    @staticmethod
    def select_best_directory(pattern: str, file_extension: str = "*.txt") -> Optional[str]:
        """
        选择最佳目录
        
        Args:
            pattern: 目录匹配模式，如 "temp_uploads/Web_example_*"
            file_extension: 文件扩展名模式，默认 "*.txt"
            
        Returns:
            最佳目录路径，如果没有找到则返回 None
        """
        matching_dirs = glob.glob(pattern)
        if not matching_dirs:
            logger.warning(f"🔍 未找到匹配的目录: {pattern}")
            return None
        
        logger.info(f"🔍 找到 {len(matching_dirs)} 个匹配目录")
        
        # 优先选择有文件的目录
        dirs_with_files = []
        for dir_path in matching_dirs:
            files_in_dir = glob.glob(os.path.join(dir_path, file_extension))
            dir_name = os.path.basename(dir_path)
            
            if files_in_dir:
                dirs_with_files.append((dir_path, len(files_in_dir)))
                logger.info(f"   📄 {dir_name}: {len(files_in_dir)} 个文件")
            else:
                logger.info(f"   📭 {dir_name}: 0 个文件")
        
        if dirs_with_files:
            # 选择文件最多的目录，如果文件数相同则选择最新的
            selected_dir = max(dirs_with_files, key=lambda x: (x[1], os.path.getctime(x[0])))[0]
            file_count = max(dirs_with_files, key=lambda x: (x[1], os.path.getctime(x[0])))[1]
            logger.info(f"✅ 选择有文件的目录: {os.path.basename(selected_dir)} (包含 {file_count} 个文件)")
            return selected_dir
        else:
            # 如果所有目录都没有文件，选择最新的目录
            latest_dir = max(matching_dirs, key=os.path.getctime)
            logger.warning(f"⚠️ 所有目录都为空，选择最新目录: {os.path.basename(latest_dir)}")
            return latest_dir
    
    @staticmethod
    def get_files_from_directory(directory: str, file_extension: str = "*.txt") -> List[str]:
        """
        从目录获取文件列表
        
        Args:
            directory: 目录路径
            file_extension: 文件扩展名模式，默认 "*.txt"
            
        Returns:
            文件路径列表
        """
        if not directory or not os.path.exists(directory):
            logger.warning(f"⚠️ 目录不存在: {directory}")
            return []
        
        files = glob.glob(os.path.join(directory, file_extension))
        logger.info(f"📁 从目录 {os.path.basename(directory)} 获取 {len(files)} 个文件")
        return files
    
    @staticmethod
    def select_best_directory_with_files(pattern: str, file_extension: str = "*.txt") -> Tuple[Optional[str], List[str]]:
        """
        选择最佳目录并返回文件列表
        
        Args:
            pattern: 目录匹配模式
            file_extension: 文件扩展名模式
            
        Returns:
            (选择的目录路径, 文件列表)
        """
        selected_dir = DirectorySelector.select_best_directory(pattern, file_extension)
        if selected_dir:
            files = DirectorySelector.get_files_from_directory(selected_dir, file_extension)
            return selected_dir, files
        else:
            return None, []

# 向后兼容的函数
def select_best_web_crawl_directory(domain: str, base_path: str = "temp_uploads") -> Tuple[Optional[str], List[str]]:
    """
    选择最佳的网页抓取目录
    
    Args:
        domain: 域名，如 "example_com"
        base_path: 基础路径，默认 "temp_uploads"
        
    Returns:
        (选择的目录路径, 文件列表)
    """
    pattern = os.path.join(base_path, f"Web_{domain}_*")
    return DirectorySelector.select_best_directory_with_files(pattern, "*.txt")

def select_best_directory_simple(pattern: str) -> Optional[str]:
    """
    简单的目录选择函数（向后兼容）
    
    Args:
        pattern: 目录匹配模式
        
    Returns:
        最佳目录路径
    """
    return DirectorySelector.select_best_directory(pattern)

if __name__ == "__main__":
    # 测试代码
    logger.info("🧪 测试智能目录选择器")
    
    # 测试网页抓取目录选择
    domain = "help_aliyun_com"
    selected_dir, files = select_best_web_crawl_directory(domain)
    
    if selected_dir:
        logger.success(selected_dir)
        logger.info(f"📁 文件数量: {len(files)}")
    else:
        logger.info("❌ 未找到有效目录")
