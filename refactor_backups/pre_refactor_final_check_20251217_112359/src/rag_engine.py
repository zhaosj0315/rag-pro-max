"""
RAG Pro Max - RAG 核心引擎
提取自 apppro.py，负责知识库的创建、加载和查询
"""

import os
import time
import shutil
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from llama_index.core import (
    VectorStoreIndex, 
    StorageContext, 
    load_index_from_storage,
    Settings
)
from llama_index.core.schema import Document


class RAGEngine:
    """RAG 核心引擎"""
    
    def __init__(
        self, 
        kb_name: str,
        persist_dir: str,
        embed_model,
        llm_model,
        logger=None
    ):
        """
        初始化 RAG 引擎
        
        Args:
            kb_name: 知识库名称
            persist_dir: 持久化目录
            embed_model: 嵌入模型
            llm_model: LLM 模型
            logger: 日志记录器
        """
        self.kb_name = kb_name
        self.persist_dir = persist_dir
        self.embed_model = embed_model
        self.llm_model = llm_model
        self.logger = logger
        self.index = None
        
        # 设置全局模型
        if embed_model:
            Settings.embed_model = embed_model
        if llm_model:
            Settings.llm = llm_model
    
    def load_existing_index(self) -> bool:
        """
        加载已有索引
        
        Returns:
            bool: 是否成功加载
        """
        if not os.path.exists(self.persist_dir):
            return False
        
        try:
            if self.logger:
                self.logger.info(f"📂 加载现有索引: {self.kb_name}")
            
            storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
            self.index = load_index_from_storage(storage_context)
            
            if self.logger:
                self.logger.success("✅ 索引加载成功")
            
            return True
            
        except Exception as e:
            error_msg = str(e)
            if self.logger:
                if "shapes" in error_msg and "not aligned" in error_msg:
                    self.logger.warning("⚠️  向量维度不匹配，需要重建索引")
                else:
                    self.logger.warning(f"⚠️  索引加载失败: {error_msg}")
            
            # 清理损坏的索引
            shutil.rmtree(self.persist_dir, ignore_errors=True)
            self.index = None
            return False
    
    def create_index(
        self, 
        documents: List[Document],
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        show_progress: bool = True
    ) -> VectorStoreIndex:
        """
        创建向量索引
        
        Args:
            documents: 文档列表
            chunk_size: 分块大小
            chunk_overlap: 分块重叠
            show_progress: 是否显示进度
            
        Returns:
            VectorStoreIndex: 创建的索引
        """
        if self.logger:
            self.logger.info(f"🔨 创建向量索引: {len(documents)} 个文档")
        
        start_time = time.time()
        
        # 创建索引
        if self.index:
            # 追加到现有索引
            if self.logger:
                self.logger.info("📝 追加文档到现有索引")
            for doc in documents:
                self.index.insert(doc)
        else:
            # 创建新索引
            if self.logger:
                self.logger.info("🆕 创建新索引")
            self.index = VectorStoreIndex.from_documents(
                documents,
                show_progress=show_progress
            )
        
        # 持久化
        self.index.storage_context.persist(persist_dir=self.persist_dir)
        
        elapsed = time.time() - start_time
        if self.logger:
            self.logger.success(f"✅ 索引创建完成 (耗时 {elapsed:.1f}s)")
        
        return self.index
    
    def get_retriever(self, similarity_top_k: int = 5):
        """
        获取检索器
        
        Args:
            similarity_top_k: 返回的相似文档数量
            
        Returns:
            检索器对象
        """
        if not self.index:
            raise ValueError("索引未加载，请先创建或加载索引")
        
        return self.index.as_retriever(similarity_top_k=similarity_top_k)
    
    def get_query_engine(
        self, 
        similarity_top_k: int = 5,
        streaming: bool = True
    ):
        """
        获取查询引擎
        
        Args:
            similarity_top_k: 返回的相似文档数量
            streaming: 是否启用流式输出
            
        Returns:
            查询引擎对象
        """
        if not self.index:
            raise ValueError("索引未加载，请先创建或加载索引")
        
        return self.index.as_query_engine(
            similarity_top_k=similarity_top_k,
            streaming=streaming
        )
    
    def get_chat_engine(
        self,
        chat_mode: str = "condense_plus_context",
        memory=None,
        similarity_top_k: int = 5,
        streaming: bool = True
    ):
        """
        获取对话引擎
        
        Args:
            chat_mode: 对话模式
            memory: 对话记忆
            similarity_top_k: 返回的相似文档数量
            streaming: 是否启用流式输出
            
        Returns:
            对话引擎对象
        """
        if not self.index:
            raise ValueError("索引未加载，请先创建或加载索引")
        
        return self.index.as_chat_engine(
            chat_mode=chat_mode,
            memory=memory,
            similarity_top_k=similarity_top_k,
            streaming=streaming
        )
    
    def query(
        self, 
        question: str,
        top_k: int = 5,
        streaming: bool = True
    ):
        """
        查询知识库
        
        Args:
            question: 查询问题
            top_k: 返回的相似文档数量
            streaming: 是否启用流式输出
            
        Returns:
            查询响应
        """
        if not self.index:
            raise ValueError("索引未加载，请先创建或加载索引")
        
        if self.logger:
            self.logger.info(f"🔍 查询: {question[:50]}...")
        
        query_engine = self.get_query_engine(
            similarity_top_k=top_k,
            streaming=streaming
        )
        
        start_time = time.time()
        response = query_engine.query(question)
        elapsed = time.time() - start_time
        
        if self.logger:
            self.logger.success(f"✅ 查询完成 (耗时 {elapsed:.1f}s)")
        
        return response
    
    def get_stats(self) -> Dict:
        """
        获取知识库统计信息
        
        Returns:
            Dict: 统计信息
        """
        if not self.index:
            return {
                "status": "未加载",
                "documents": 0,
                "nodes": 0
            }
        
        try:
            docstore = self.index.docstore
            nodes = list(docstore.docs.values())
            
            return {
                "status": "已加载",
                "documents": len(set(n.ref_doc_id for n in nodes if hasattr(n, 'ref_doc_id'))),
                "nodes": len(nodes),
                "persist_dir": self.persist_dir
            }
        except:
            return {
                "status": "已加载",
                "persist_dir": self.persist_dir
            }
    
    def delete(self):
        """删除知识库"""
        if os.path.exists(self.persist_dir):
            shutil.rmtree(self.persist_dir)
            if self.logger:
                self.logger.success(f"✅ 知识库已删除: {self.kb_name}")
        
        self.index = None
    
    def __repr__(self):
        stats = self.get_stats()
        return f"RAGEngine(kb_name='{self.kb_name}', status='{stats['status']}')"
