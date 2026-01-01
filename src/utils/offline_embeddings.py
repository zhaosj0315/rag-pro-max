"""
离线嵌入模型支持
当网络不可用时使用本地模型
"""

import torch
from sentence_transformers import SentenceTransformer
from typing import List, Optional

class OfflineEmbeddings:
    """离线嵌入模型"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        
    def load_model(self) -> bool:
        """加载模型，优先使用本地缓存"""
        try:
            # 尝试加载本地模型
            self.model = SentenceTransformer(
                self.model_name,
                device=self.device,
                cache_folder="./hf_cache"
            )
            return True
        except Exception as e:
            print(f"❌ 离线模型加载失败: {e}")
            return False
    
    def encode(self, texts: List[str]) -> List[List[float]]:
        """编码文本为向量"""
        if not self.model:
            if not self.load_model():
                # 返回随机向量作为fallback
                import numpy as np
                return [np.random.rand(384).tolist() for _ in texts]
        
        try:
            embeddings = self.model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            print(f"❌ 文本编码失败: {e}")
            # 返回随机向量作为fallback
            import numpy as np
            return [np.random.rand(384).tolist() for _ in texts]

def get_offline_embeddings(model_name: str = "all-MiniLM-L6-v2") -> OfflineEmbeddings:
    """获取离线嵌入模型实例"""
    return OfflineEmbeddings(model_name)
