"""
多模态向量化模块 - v2.1
支持图片内容向量表示、表格结构向量化、跨模态检索
"""

import numpy as np
import torch
from PIL import Image
import pandas as pd
from typing import Dict, List, Optional, Union, Any
import cv2
import logging

# 尝试导入CLIP相关模块
try:
    from transformers import CLIPProcessor, CLIPModel
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    logging.warning("CLIP模型不可用，图片向量化功能将被禁用")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("SentenceTransformers不可用，文本向量化功能将被禁用")

class MultiModalVectorizer:
    """多模态向量化器"""
    
    def __init__(self, 
                 text_model_name: str = "BAAI/bge-small-zh-v1.5",
                 vision_model_name: str = "openai/clip-vit-base-patch32"):
        
        # 文本嵌入模型
        self.text_model = None
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.text_model = SentenceTransformer(text_model_name)
            except Exception as e:
                logging.warning(f"文本模型加载失败: {e}")
        
        # 视觉嵌入模型
        self.vision_model = None
        self.vision_processor = None
        if CLIP_AVAILABLE:
            try:
                self.vision_model = CLIPModel.from_pretrained(vision_model_name)
                self.vision_processor = CLIPProcessor.from_pretrained(vision_model_name)
                self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
                self.vision_model.to(self.device)
            except Exception as e:
                logging.warning(f"视觉模型加载失败: {e}")
        
        # 向量维度
        self.text_dim = 512  # bge-small-zh-v1.5
        self.vision_dim = 512  # CLIP
        self.unified_dim = 512  # 统一向量维度
    
    def encode_text(self, text: str) -> Optional[np.ndarray]:
        """文本向量化"""
        if not self.text_model or not text.strip():
            return None
        
        try:
            vector = self.text_model.encode(text, normalize_embeddings=True)
            return vector.astype(np.float32)
        except Exception as e:
            logging.error(f"文本向量化失败: {e}")
            return None
    
    def encode_image(self, image_path: str) -> Optional[np.ndarray]:
        """图片向量化"""
        if not self.vision_model or not self.vision_processor:
            return None
        
        try:
            # 加载图片
            image = Image.open(image_path).convert('RGB')
            
            # 预处理
            inputs = self.vision_processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 获取图片特征
            with torch.no_grad():
                image_features = self.vision_model.get_image_features(**inputs)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy().flatten().astype(np.float32)
            
        except Exception as e:
            logging.error(f"图片向量化失败: {e}")
            return None
    
    def encode_table_structure(self, table_structure: Dict) -> Optional[np.ndarray]:
        """表格结构向量化"""
        try:
            # 构建结构描述文本
            structure_text = self._structure_to_text(table_structure)
            return self.encode_text(structure_text)
        except Exception as e:
            logging.error(f"表格结构向量化失败: {e}")
            return None
    
    def encode_table_content(self, table_data: pd.DataFrame, 
                           max_rows: int = 100) -> List[Dict]:
        """表格内容向量化"""
        content_vectors = []
        
        try:
            # 限制行数避免内存问题
            sample_data = table_data.head(max_rows) if len(table_data) > max_rows else table_data
            
            for idx, row in sample_data.iterrows():
                # 构建行文本
                row_text = self._row_to_text(row, table_data.columns)
                
                # 向量化
                vector = self.encode_text(row_text)
                if vector is not None:
                    content_vectors.append({
                        'row_id': idx,
                        'vector': vector,
                        'text': row_text,
                        'data': row.to_dict()
                    })
        
        except Exception as e:
            logging.error(f"表格内容向量化失败: {e}")
        
        return content_vectors
    
    def create_multimodal_vector(self, 
                                text_vector: Optional[np.ndarray] = None,
                                image_vector: Optional[np.ndarray] = None,
                                table_vector: Optional[np.ndarray] = None,
                                weights: Dict[str, float] = None) -> Optional[np.ndarray]:
        """创建多模态融合向量"""
        
        if weights is None:
            weights = {'text': 0.5, 'image': 0.3, 'table': 0.2}
        
        vectors = []
        vector_weights = []
        
        # 收集有效向量
        if text_vector is not None:
            vectors.append(self._normalize_vector(text_vector))
            vector_weights.append(weights.get('text', 0.5))
        
        if image_vector is not None:
            vectors.append(self._normalize_vector(image_vector))
            vector_weights.append(weights.get('image', 0.3))
        
        if table_vector is not None:
            vectors.append(self._normalize_vector(table_vector))
            vector_weights.append(weights.get('table', 0.2))
        
        if not vectors:
            return None
        
        # 加权融合
        try:
            # 确保所有向量维度一致
            unified_vectors = [self._resize_vector(v, self.unified_dim) for v in vectors]
            
            # 加权平均
            weighted_sum = np.zeros(self.unified_dim, dtype=np.float32)
            total_weight = 0
            
            for vector, weight in zip(unified_vectors, vector_weights):
                weighted_sum += vector * weight
                total_weight += weight
            
            if total_weight > 0:
                fused_vector = weighted_sum / total_weight
                return self._normalize_vector(fused_vector)
            
        except Exception as e:
            logging.error(f"多模态向量融合失败: {e}")
        
        return None
    
    def cross_modal_similarity(self, 
                              query_vector: np.ndarray,
                              candidate_vectors: List[Dict],
                              similarity_threshold: float = 0.7) -> List[Dict]:
        """跨模态相似度计算"""
        results = []
        
        try:
            query_norm = self._normalize_vector(query_vector)
            
            for candidate in candidate_vectors:
                candidate_vector = candidate.get('vector')
                if candidate_vector is None:
                    continue
                
                candidate_norm = self._normalize_vector(candidate_vector)
                
                # 计算余弦相似度
                similarity = np.dot(query_norm, candidate_norm)
                
                if similarity >= similarity_threshold:
                    results.append({
                        'content': candidate,
                        'similarity': float(similarity),
                        'modality': candidate.get('modality', 'unknown')
                    })
            
            # 按相似度排序
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
        except Exception as e:
            logging.error(f"跨模态相似度计算失败: {e}")
        
        return results
    
    def _structure_to_text(self, structure: Dict) -> str:
        """表格结构转文本描述"""
        text_parts = []
        
        # 基本信息
        text_parts.append(f"表格包含{structure.get('rows', 0)}行{structure.get('columns', 0)}列")
        
        # 列信息
        headers = structure.get('headers', [])
        if headers:
            text_parts.append(f"列名包括: {', '.join(headers)}")
        
        # 数据类型
        data_types = structure.get('data_types', {})
        if data_types:
            type_desc = []
            for col, dtype in data_types.items():
                type_desc.append(f"{col}为{dtype}类型")
            text_parts.append(' '.join(type_desc))
        
        # 语义信息
        semantic_info = structure.get('semantic_info', {})
        if semantic_info.get('title_candidates'):
            text_parts.append(f"主要标识列: {', '.join(semantic_info['title_candidates'])}")
        
        return ' '.join(text_parts)
    
    def _row_to_text(self, row: pd.Series, columns: List[str]) -> str:
        """表格行转文本"""
        text_parts = []
        
        for col in columns:
            value = row[col]
            if pd.notna(value):
                text_parts.append(f"{col}: {value}")
        
        return ' '.join(text_parts)
    
    def _normalize_vector(self, vector: np.ndarray) -> np.ndarray:
        """向量归一化"""
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm
    
    def _resize_vector(self, vector: np.ndarray, target_dim: int) -> np.ndarray:
        """调整向量维度"""
        current_dim = len(vector)
        
        if current_dim == target_dim:
            return vector
        elif current_dim > target_dim:
            # 截断
            return vector[:target_dim]
        else:
            # 填充零
            padded = np.zeros(target_dim, dtype=vector.dtype)
            padded[:current_dim] = vector
            return padded

class CrossModalRetriever:
    """跨模态检索器"""
    
    def __init__(self, vectorizer: MultiModalVectorizer):
        self.vectorizer = vectorizer
        self.content_store = {
            'text': [],
            'image': [],
            'table': [],
            'multimodal': []
        }
    
    def add_content(self, content_type: str, content_data: Dict):
        """添加内容到存储"""
        if content_type in self.content_store:
            self.content_store[content_type].append(content_data)
    
    def search(self, query: str, 
              modalities: List[str] = None,
              top_k: int = 5,
              similarity_threshold: float = 0.7) -> List[Dict]:
        """跨模态搜索"""
        
        if modalities is None:
            modalities = ['text', 'image', 'table', 'multimodal']
        
        # 查询向量化
        query_vector = self.vectorizer.encode_text(query)
        if query_vector is None:
            return []
        
        all_results = []
        
        # 在各模态中搜索
        for modality in modalities:
            if modality in self.content_store:
                candidates = self.content_store[modality]
                results = self.vectorizer.cross_modal_similarity(
                    query_vector, candidates, similarity_threshold
                )
                
                # 添加模态标识
                for result in results:
                    result['source_modality'] = modality
                
                all_results.extend(results)
        
        # 全局排序
        all_results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return all_results[:top_k]
    
    def get_statistics(self) -> Dict:
        """获取存储统计信息"""
        stats = {}
        for modality, contents in self.content_store.items():
            stats[modality] = len(contents)
        return stats
