"""
RAG Pro Max - RAG 核心引擎
提取自 apppro.py，负责知识库的创建、加载和查询
"""

import os
import time
import shutil
from typing import List, Dict, Optional
from llama_index.core import (
    VectorStoreIndex, 
    StorageContext, 
    load_index_from_storage,
    Settings,
    PromptTemplate
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
        """
        if not os.path.exists(self.persist_dir):
            return False
        
        # 检查是否为纯数据分析库 (只有 SQL DB, 没向量库)
        db_path = os.path.join(self.persist_dir, "business_data.db")
        docstore_path = os.path.join(self.persist_dir, "docstore.json")
        
        try:
            # 关键：如果核心向量文件不全，直接视为纯数据分析模式，不调用 StorageContext
            if not os.path.exists(docstore_path) or not os.path.exists(os.path.join(self.persist_dir, "vector_store.json")):
                if os.path.exists(db_path):
                    if self.logger:
                        self.logger.warning(f"⚠️  未发现完整向量索引，已切换至【纯数据分析】模式")
                    self.index = None # 标记没有向量索引
                    return True
                else:
                    return False

            # 只有文件齐全才尝试加载
            storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
            self.index = load_index_from_storage(storage_context)
            
            if self.logger:
                self.logger.success("✅ 向量索引加载成功")
            return True
            
        except Exception as e:
            if os.path.exists(db_path):
                if self.logger: self.logger.warning(f"⚠️  索引加载异常，降级至纯数据模式: {e}")
                self.index = None
                return True
            return False
            
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
        
        # 定义中文问答模板 (优化 Gemini/DeepSeek 等模型的指令遵循)
        qa_prompt_tmpl_str = (
            "以下是已知信息：\n"
            "---------------------\n"
            "{context_str}\n"
            "---------------------\n"
            "请完全根据上述上下文信息回答用户的问题。不要使用外部知识。\n"
            "如果上下文中包含相关信息，请详细回答。\n"
            "如果上下文中没有相关信息，请回答“知识库中未找到相关内容”。\n"
            "问题：{query_str}\n"
            "回答："
        )
        qa_prompt_tmpl = PromptTemplate(qa_prompt_tmpl_str)
        
        return self.index.as_query_engine(
            similarity_top_k=similarity_top_k,
            streaming=streaming,
            text_qa_template=qa_prompt_tmpl,
            llm=self.llm_model
        )

    def get_chat_engine(
        self,
        chat_mode: str = "context",
        similarity_top_k: int = 5,
        streaming: bool = True
    ):
        """
        获取聊天引擎
        
        Args:
            chat_mode: 聊天模式 ("context", "condense_question", "simple")
            similarity_top_k: 返回的相似文档数量
            streaming: 是否启用流式输出
            
        Returns:
            聊天引擎对象
        """
        if not self.index:
            raise ValueError("索引未加载，请先创建或加载索引")
            
        from llama_index.core.memory import ChatMemoryBuffer
        
        return self.index.as_chat_engine(
            chat_mode=chat_mode,
            memory=ChatMemoryBuffer.from_defaults(token_limit=2000),
            similarity_top_k=similarity_top_k,
            streaming=streaming,
            system_prompt="你是一个精准的知识库助手，请务必仅基于提供的上下文和知识回答问题。如果知识库中没有相关信息，请明确指出。回答应清晰、简洁、专业。",
            llm=self.llm_model
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


def create_rag_engine(kb_name: str, logger=None) -> Optional['RAGEngine']:
    """
    创建 RAGEngine 实例的工厂函数
    
    Args:
        kb_name: 知识库名称
        logger: 日志记录器
        
    Returns:
        RAGEngine 实例，如果创建失败则返回 None
    """
    try:
        from src.core.app_config import load_config, output_base
        from src.utils.model_manager import load_embedding_model, load_llm_model
        from src.config.manifest_manager import ManifestManager
        
        # 加载全局配置
        config = load_config()
        persist_dir = os.path.join(output_base, kb_name)
        
        # --- 核心补丁：元数据自动纠错 ---
        manifest = ManifestManager.load(persist_dir)
        kb_embed_model = manifest.get('embed_model')
        kb_embed_provider = manifest.get('embed_provider')
        
        # 如果知识库元数据中模型是 Unknown，则强制使用全局配置模型
        if not kb_embed_model or kb_embed_model == "Unknown":
            kb_embed_model = config.get('embed_model') or "sentence-transformers/all-MiniLM-L6-v2"
            kb_embed_provider = config.get('embed_provider') or "HuggingFace (本地/极速)"
            if logger:
                logger.warning(f"⚠️ 检测到损坏的元数据(Unknown)，已自动纠错为系统默认模型: {kb_embed_model}")
        
        # 确保配置值有效 (LLM)
        llm_provider = config.get('llm_provider') or "Ollama"
        llm_model_name = config.get('llm_model') or "gpt-oss:20b"
        
        # 加载 Embedding 模型 (优先使用纠错后的知识库配置)
        embed_model = load_embedding_model(
            provider=kb_embed_provider,
            model_name=kb_embed_model,
            api_key=config.get('embed_key'),
            api_url=config.get('embed_url')
        )
        
        # 加载 LLM 模型
        llm_model = load_llm_model(
            provider=llm_provider,
            model_name=llm_model_name,
            api_key=config.get('llm_key'),
            api_url=config.get('llm_url'),
            temperature=config.get('temperature', 0.7)
        )
        
        # 创建引擎实例
        engine = RAGEngine(
            kb_name=kb_name,
            persist_dir=persist_dir,
            embed_model=embed_model,
            llm_model=llm_model,
            logger=logger
        )
        
        # 加载已有索引
        if engine.load_existing_index():
            # 补丁：即使 engine.index 为 None (纯数据分析模式)，也视为挂载成功
            return engine
        else:
            if logger:
                logger.error(f"❌ 无法加载知识库索引: {kb_name}")
            return None
            
    except Exception as e:
        if logger:
            logger.error(f"❌ 创建 RAG 引擎失败: {str(e)}")
        return None