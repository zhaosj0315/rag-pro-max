"""
简化终端输出日志记录器 - 避免递归问题
"""

# 使用LogManager
try:
    from src.app_logging.log_manager import LogManager
    logger = LogManager()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

def log_terminal_output(message, level="info"):
    """简单的终端输出日志记录"""
    try:
        if hasattr(logger, 'log'):
            logger.log(level, f"🖥️ [终端输出] {message}")
        else:
            getattr(logger, level, logger.info)(f"🖥️ [终端输出] {message}")
    except Exception:
        # 避免日志记录失败影响主程序
        pass

# 替换print函数的简单版本
original_print = print

def enhanced_print(*args, **kwargs):
    """增强的print函数，同时记录到日志"""
    # 先正常输出到终端
    original_print(*args, **kwargs)
    
    # 然后记录到日志（避免递归）
    try:
        message = ' '.join(str(arg) for arg in args)
        if message.strip() and not message.startswith('📝'):  # 避免记录日志消息本身
            log_terminal_output(message)
    except Exception:
        # 如果日志记录失败，不影响正常输出
        pass
