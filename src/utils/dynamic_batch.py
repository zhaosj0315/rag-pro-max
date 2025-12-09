"""
动态批量优化 - Dynamic Batch Optimization
根据文档数量和可用内存动态调整batch size
"""

import psutil
import torch


class DynamicBatchOptimizer:
    """动态批量优化器"""
    
    def __init__(self, embedding_dim: int = 1024, safety_factor: float = 0.8):
        self.embedding_dim = embedding_dim
        self.safety_factor = safety_factor
        self.device = self._detect_device()
    
    def _detect_device(self) -> str:
        """检测可用设备"""
        if torch.cuda.is_available():
            return 'cuda'
        elif torch.backends.mps.is_available():
            return 'mps'
        else:
            return 'cpu'
    
    def get_available_memory(self) -> float:
        """获取可用内存（GB）"""
        if self.device == 'cuda':
            # CUDA设备，检查GPU显存
            try:
                import torch
                gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                gpu_free = (torch.cuda.get_device_properties(0).total_memory - 
                           torch.cuda.memory_allocated(0)) / (1024**3)
                return min(gpu_free, gpu_mem * 0.8)  # 最多使用80%
            except:
                return psutil.virtual_memory().available / (1024**3)
        elif self.device == 'mps':
            # M4 Max 有专用的统一内存，但需要保守估计
            total_mem = psutil.virtual_memory().total / (1024**3)
            available_mem = psutil.virtual_memory().available / (1024**3)
            # MPS使用统一内存，预留更多给系统
            return min(available_mem, total_mem * 0.6)
        else:
            return psutil.virtual_memory().available / (1024**3)
    
    def calculate_batch_size(self, doc_count: int, avg_doc_size: int = 1000) -> int:
        """
        计算最优batch size
        
        Args:
            doc_count: 文档数量
            avg_doc_size: 平均文档大小（字符数）
        
        Returns:
            最优batch size
        """
        available_memory = self.get_available_memory()
        
        # 小批量：快速响应
        if doc_count < 10:
            return 512
        
        # 中批量：平衡性能
        elif doc_count < 100:
            return 2048
        
        # 大批量：根据内存动态调整
        else:
            # 估算每个embedding需要的内存（MB）
            memory_per_embedding = (self.embedding_dim * 4) / (1024**2)  # float32
            
            # 计算最大batch size
            max_batch = int((available_memory * 1024 * self.safety_factor) / memory_per_embedding)
            
            # 限制在合理范围内
            return min(max(max_batch, 512), 4096)
    
    def get_optimal_config(self, doc_count: int) -> dict:
        """
        获取最优配置
        
        Returns:
            配置字典
        """
        batch_size = self.calculate_batch_size(doc_count)
        
        return {
            'batch_size': batch_size,
            'device': self.device,
            'available_memory_gb': self.get_available_memory(),
            'embedding_dim': self.embedding_dim,
            'doc_count': doc_count
        }
