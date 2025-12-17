"""
自定义嵌入模型 - 支持大 batch_size，绕过 LlamaIndex 限制
"""
from typing import List
import torch
from transformers import AutoTokenizer, AutoModel
from llama_index.core.embeddings import BaseEmbedding


class CustomHuggingFaceEmbedding(BaseEmbedding):
    """自定义 HuggingFace 嵌入，支持大 batch_size"""
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        cache_folder: str = "./hf_cache",
        batch_size: int = 2048,
        device: str = "mps"
    ):
        super().__init__()
        self._model_name = model_name
        self._batch_size = batch_size
        self._device = device
        
        print(f"🔄 加载模型: {model_name}")
        print(f"📦 Batch Size: {batch_size}")
        print(f"🎮 设备: {device}")
        
        # 加载模型和分词器
        self._tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=cache_folder
        )
        self._model = AutoModel.from_pretrained(
            model_name,
            cache_dir=cache_folder
        ).to(device)
        self._model.eval()
        
        # 优化GPU利用率
        if device in ["mps", "cuda"]:
            try:
                # PyTorch 2.0+ 编译优化
                if hasattr(torch, 'compile'):
                    self._model = torch.compile(self._model, mode="max-autotune")
                    print(f"🚀 已启用 torch.compile 加速")
            except:
                pass
        
        print(f"✅ 模型加载完成")
    
    def _mean_pooling(self, model_output, attention_mask):
        """平均池化"""
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """获取查询嵌入"""
        return self._get_text_embedding(query)
    
    def _get_text_embedding(self, text: str) -> List[float]:
        """获取文本嵌入"""
        return self._get_text_embeddings([text])[0]
    
    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量获取文本嵌入 - 支持大 batch_size，优化GPU利用率"""
        all_embeddings = []
        
        # 分批处理
        for i in range(0, len(texts), self._batch_size):
            batch_texts = texts[i:i + self._batch_size]
            
            # 编码（使用 pin_memory 加速传输）
            encoded_input = self._tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors='pt'
            )
            
            # 优化数据传输
            if self._device == "cuda":
                encoded_input = {k: v.pin_memory().to(self._device, non_blocking=True) 
                               for k, v in encoded_input.items()}
            else:
                encoded_input = {k: v.to(self._device) for k, v in encoded_input.items()}
            
            # 推理
            with torch.no_grad():
                model_output = self._model(**encoded_input)
            
            # 池化
            embeddings = self._mean_pooling(model_output, encoded_input['attention_mask'])
            
            # 归一化
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
            
            # 转换为列表
            all_embeddings.extend(embeddings.cpu().tolist())
        
        return all_embeddings
    
    async def _aget_query_embedding(self, query: str) -> List[float]:
        """异步获取查询嵌入"""
        return self._get_query_embedding(query)
    
    async def _aget_text_embedding(self, text: str) -> List[float]:
        """异步获取文本嵌入"""
        return self._get_text_embedding(text)


def create_custom_embedding(
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    cache_folder: str = "./hf_cache",
    batch_size: int = 2048,
    device: str = "mps"
) -> CustomHuggingFaceEmbedding:
    """创建自定义嵌入模型"""
    return CustomHuggingFaceEmbedding(
        model_name=model_name,
        cache_folder=cache_folder,
        batch_size=batch_size,
        device=device
    )
