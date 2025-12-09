"""
内存和显存管理模块
"""

def cleanup_memory():
    """清理内存和显存缓存"""
    import gc
    gc.collect()
    
    try:
        import torch
        # 延迟导入，避免 pickle 错误
        try:
            from src.logging import LogManager
            logger = LogManager()
        except:
            logger = None
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            if logger:
                logger.info("🧹 已清理 CUDA 显存缓存")
        elif torch.backends.mps.is_available():
            torch.mps.empty_cache()
            if logger:
                logger.info("🧹 已清理 MPS 显存缓存")
    except Exception as e:
        try:
            from src.logging import LogManager
            logger = LogManager()
            if logger:
                logger.warning(f"显存清理失败: {e}")
        except:
            pass


def get_memory_stats():
    """获取内存统计信息"""
    try:
        import psutil
        
        mem = psutil.virtual_memory()
        stats = {
            'total': mem.total / (1024**3),  # GB
            'available': mem.available / (1024**3),
            'used': mem.used / (1024**3),
            'percent': mem.percent
        }
        
        # GPU 内存
        try:
            import torch
            if torch.cuda.is_available():
                stats['gpu_allocated'] = torch.cuda.memory_allocated() / (1024**3)
                stats['gpu_reserved'] = torch.cuda.memory_reserved() / (1024**3)
            elif torch.backends.mps.is_available():
                stats['gpu_type'] = 'MPS'
        except:
            pass
        
        return stats
    except Exception as e:
        return {'error': str(e)}
