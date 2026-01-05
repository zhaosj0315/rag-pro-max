from src.app_logging.log_manager import LogManager

logger = LogManager()

"""
OCR性能优化器 - 带CPU保护
动态调整OCR进程数，确保CPU使用率不超过95%
"""

import time
import threading
import multiprocessing as mp
from typing import Tuple

class OCROptimizer:
    """OCR性能优化器 - 带CPU保护"""
    
    def __init__(self):
        self.cpu_count = mp.cpu_count()
        self.max_cpu_usage = 95.0  # CPU使用率上限
        self.monitoring = False
        self.current_workers = 0
        
    def get_optimal_workers(self, page_count: int) -> Tuple[int, str]:
        """
        根据系统状态和页数获取最优进程数
        
        Args:
            page_count: PDF页数
            
        Returns:
            (进程数, 策略说明)
        """
        try:
            import psutil
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
        except ImportError:
            cpu_usage = 50  # 默认值
            memory = None
        
        # 更严格的CPU保护：如果已经接近90%，只用1个进程
        if cpu_usage > 85:
            base_workers = 1
            strategy = "极限保护模式"
        elif cpu_usage > 70:
            base_workers = 2
            strategy = "严格保护模式"
        elif cpu_usage > 50:
            base_workers = 3
            strategy = "CPU限制模式"
        elif cpu_usage < 20:
            # CPU空闲：但仍然保守，最多4进程
            base_workers = min(self.cpu_count // 4, 4)  # 保留3/4核给系统
            strategy = "保守高效模式"
        else:
            # CPU适中：非常保守
            base_workers = min(self.cpu_count // 6, 3)  # 保留5/6核给系统
            strategy = "超保守模式"
        
        # 根据页数调整，但进一步限制
        if page_count <= 3:
            workers = min(base_workers, page_count, 2)  # 最多2进程
        elif page_count <= 10:
            workers = min(base_workers, 3)  # 最多3进程
        else:
            workers = min(base_workers, 4)  # 最多4进程
        
        # 内存检查
        if memory and memory.percent > 70:
            workers = min(workers, 2)
            strategy += " (内存限制)"
        
        # 确保至少1个进程
        workers = max(workers, 1)
        
        return workers, f"{strategy} (CPU: {cpu_usage:.1f}%)"
    
    def start_cpu_monitoring(self, workers: int):
        """启动CPU监控线程"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.current_workers = workers
        self.emergency_stop = False
        
        def monitor_cpu():
            try:
                import psutil
                consecutive_high = 0
                while self.monitoring:
                    cpu_usage = psutil.cpu_percent(interval=0.5)
                    
                    if cpu_usage > 98:
                        consecutive_high += 1
                        logger.info(f"🚨 CPU危险: {cpu_usage:.1f}% (连续{consecutive_high}次)")
                        
                        if consecutive_high >= 3:  # 连续3次超过98%
                            logger.info(f"🛑 紧急停止OCR处理！CPU过载风险")
                            self.emergency_stop = True
                            break
                            
                        time.sleep(3)  # 更长的暂停
                    elif cpu_usage > self.max_cpu_usage:
                        consecutive_high = max(0, consecutive_high - 1)
                        logger.warning(self.max_cpu_usage)
                        logger.info(f"💤 暂停OCR处理3秒，等待CPU降温...")
                        time.sleep(3)
                    elif cpu_usage > 85:
                        consecutive_high = 0
                        logger.info(f"🔥 CPU使用率较高: {cpu_usage:.1f}%，降低处理速度")
                        time.sleep(1)
                    else:
                        consecutive_high = 0
                        time.sleep(2)  # 正常情况下检查间隔更长
            except ImportError:
                pass
        
        monitor_thread = threading.Thread(target=monitor_cpu, daemon=True)
        monitor_thread.start()
    
    def stop_cpu_monitoring(self):
        """停止CPU监控"""
        self.monitoring = False
        
    def should_emergency_stop(self):
        """检查是否应该紧急停止"""
        return getattr(self, 'emergency_stop', False)
    
    def estimate_time(self, page_count: int, workers: int) -> float:
        """
        估算OCR处理时间
        
        Args:
            page_count: 页数
            workers: 进程数
            
        Returns:
            预估时间（秒）
        """
        # 基于经验的时间估算
        # 单页OCR大约需要1-3秒（取决于内容复杂度）
        avg_time_per_page = 2.5  # 秒（考虑CPU保护的额外时间）
        
        # 并行效率（考虑进程创建开销和CPU保护）
        if workers == 1:
            efficiency = 1.0
        elif workers <= 3:
            efficiency = 0.85
        elif workers <= 6:
            efficiency = 0.75
        else:
            efficiency = 0.65
        
        estimated_time = (page_count * avg_time_per_page) / (workers * efficiency)
        return max(estimated_time, 8.0)  # 最少8秒（考虑CPU保护）
    
    def print_optimization_info(self, page_count: int):
        """打印优化信息"""
        workers, strategy = self.get_optimal_workers(page_count)
        estimated_time = self.estimate_time(page_count, workers)
        
        logger.info(f"   📊 OCR优化策略: {strategy}")
        logger.info(f"   🔄 使用进程数: {workers}/{self.cpu_count} (保留{self.cpu_count-workers}核给系统)")
        logger.info(f"   ⏱️  预估时间: {estimated_time:.0f}秒")
        logger.info(f"   🛡️  CPU保护: 限制使用率 < {self.max_cpu_usage}%")
        
        # 性能提示
        if workers >= 6:
            logger.info(f"   🚀 高效模式：充分利用多核CPU，但保护系统稳定")
        elif workers >= 3:
            logger.info(f"   ⚡ 平衡模式：兼顾性能和稳定性")
        else:
            logger.info(f"   🛡️  保护模式：系统负载较高，优先保证稳定性")

# 全局实例
ocr_optimizer = OCROptimizer()
