"""
资源监控工具
提取自 apppro.py
"""

import psutil


def check_resource_usage(threshold=90.0):
    """
    检查系统资源使用率
    
    Args:
        threshold: 资源使用阈值，默认90%
        
    Returns:
        tuple: (cpu%, mem%, gpu%, should_throttle)
    """
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory().percent
    gpu = 0.0
    
    # 尝试获取 GPU 使用率
    try:
        import torch
        if torch.backends.mps.is_available():
            # MPS (Apple Silicon) - 通过内存使用估算
            gpu = min(threshold, mem * 0.8)  # 粗略估算
        elif torch.cuda.is_available():
            # CUDA GPU
            if torch.cuda.max_memory_allocated() > 0:
                gpu = torch.cuda.memory_allocated() / torch.cuda.max_memory_allocated() * 100
            else:
                gpu = 0
    except:
        pass
    
    should_throttle = cpu > threshold or mem > threshold or gpu > threshold
    return cpu, mem, gpu, should_throttle


def get_system_stats():
    """
    获取系统统计信息
    
    Returns:
        dict: 系统统计信息
    """
    cpu_percent = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    stats = {
        'cpu_percent': cpu_percent,
        'cpu_count': psutil.cpu_count(),
        'memory_percent': mem.percent,
        'memory_used_gb': mem.used / (1024**3),
        'memory_total_gb': mem.total / (1024**3),
        'disk_percent': disk.percent,
        'disk_used_gb': disk.used / (1024**3),
        'disk_total_gb': disk.total / (1024**3)
    }
    
    # GPU 信息
    try:
        import torch
        if torch.backends.mps.is_available():
            stats['gpu_available'] = True
            stats['gpu_type'] = 'MPS (Apple Silicon)'
        elif torch.cuda.is_available():
            stats['gpu_available'] = True
            stats['gpu_type'] = 'CUDA'
            stats['gpu_count'] = torch.cuda.device_count()
            stats['gpu_memory_allocated_gb'] = torch.cuda.memory_allocated() / (1024**3)
            stats['gpu_memory_reserved_gb'] = torch.cuda.memory_reserved() / (1024**3)
        else:
            stats['gpu_available'] = False
    except:
        stats['gpu_available'] = False
    
    return stats


def should_throttle(cpu, mem, gpu, threshold=90.0):
    """
    判断是否需要限流
    
    Args:
        cpu: CPU 使用率
        mem: 内存使用率
        gpu: GPU 使用率
        threshold: 阈值，默认90%
        
    Returns:
        bool: 是否需要限流
    """
    return cpu > threshold or mem > threshold or gpu > threshold


def format_bytes(bytes_value):
    """
    格式化字节数
    
    Args:
        bytes_value: 字节数
        
    Returns:
        str: 格式化后的字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"
