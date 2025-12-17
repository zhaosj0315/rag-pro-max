"""
查询处理器
提取自 apppro.py 的查询处理逻辑
"""

import os
import time
import streamlit as st
from llama_index.core import Settings, load_index_from_storage, StorageContext

from src.app_logging import LogManager
from src.utils.memory import cleanup_memory
from src.utils.model_manager import load_embedding_model, load_llm_model
from src.chat import HistoryManager


class QueryHandler:
    """查询处理器"""
    
    def __init__(self):
        self.logger = LogManager()
    
    def load_knowledge_base(self, kb_name: str, output_base: str, embed_provider: str, 
                           embed_model: str, embed_key: str, embed_url: str) -> bool:
        """
        加载知识库
        
        Args:
            kb_name: 知识库名称
            output_base: 输出基础路径
            embed_provider: 嵌入模型提供商
            embed_model: 嵌入模型名称
            embed_key: API密钥
            embed_url: API地址
            
        Returns:
            bool: 加载是否成功
        """
        db_path = os.path.join(output_base, kb_name)
        if not os.path.exists(db_path):
            return False
        
        try:
            self.logger.log("INFO", f"开始加载知识库: {kb_name}", stage="知识库加载")
            
            # 检测知识库的向量维度
            kb_dim = self._get_kb_embedding_dim(db_path)
            if kb_dim:
                # 根据维度选择合适的模型
                model_map = {
                    512: "sentence-transformers/all-MiniLM-L6-v2",
                    768: "BAAI/bge-base-zh-v1.5", 
                    1024: "BAAI/bge-m3"
                }
                
                if kb_dim in model_map:
                    required_model = model_map[kb_dim]
                    if embed_model != required_model:
                        self.logger.warning(f"⚠️ 知识库维度: {kb_dim}D，自动切换模型: {required_model}")
                        embed_model = required_model
                        # 重新加载 embedding 模型
                        embed = load_embedding_model(embed_provider, embed_model, embed_key, embed_url)
                        if embed:
                            Settings.embed_model = embed
            
            # 加载向量索引
            storage_context = StorageContext.from_defaults(persist_dir=db_path)
            index = load_index_from_storage(storage_context)
            
            # 创建查询引擎
            chat_engine = index.as_chat_engine(
                chat_mode="context",
                memory=None,
                system_prompt="你是一个专业的AI助手。请基于提供的文档内容回答问题，如果文档中没有相关信息，请明确说明。",
                verbose=False
            )
            
            st.session_state.chat_engine = chat_engine
            self.logger.success(f"✅ 知识库加载成功: {kb_name}")
            
            # 清理内存
            cleanup_memory()
            self.logger.info("🧹 已清理 MPS 显存缓存")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 知识库加载失败: {str(e)}")
            return False
    
    def process_question(self, question: str, llm_provider: str, llm_model: str, 
                        llm_key: str, llm_url: str, temperature: float = 0.7):
        """
        处理用户问题
        
        Args:
            question: 用户问题
            llm_provider: LLM提供商
            llm_model: LLM模型
            llm_key: API密钥
            llm_url: API地址
            temperature: 温度参数
            
        Yields:
            dict: 处理结果
        """
        try:
            # 设置LLM
            llm = load_llm_model(llm_provider, llm_model, llm_key, llm_url, temperature)
            if llm:
                Settings.llm = llm
            
            # 开始查询
            self.logger.log("INFO", f"用户提问: {question}", stage="查询对话")
            self.logger.log("INFO", "开始检索相关文档", stage="查询对话")
            
            start_time = time.time()
            
            # 流式响应
            response = st.session_state.chat_engine.stream_chat(question)
            
            full_text = ""
            for token in response.response_gen:
                full_text += token
                yield {
                    'type': 'token',
                    'content': token
                }
            
            # 完成处理
            elapsed = time.time() - start_time
            
            # 获取源文档
            sources = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    if hasattr(node, 'metadata') and 'file_name' in node.metadata:
                        sources.append({
                            'file_name': node.metadata['file_name'],
                            'content': node.text[:200] + "..." if len(node.text) > 200 else node.text
                        })
            
            # 统计信息
            stats = {
                'elapsed_time': elapsed,
                'source_count': len(sources)
            }
            
            self.logger.success("✅ 查询对话回答生成完成")
            self.logger.log("INFO", f"完成: 查询完成 (耗时 {elapsed:.2f}s)", stage="查询对话")
            
            yield {
                'type': 'complete',
                'content': full_text,
                'sources': sources,
                'stats': stats
            }
            
        except Exception as e:
            self.logger.error(f"❌ 查询处理失败: {str(e)}")
            yield {
                'type': 'error',
                'content': str(e)
            }
    
    def _get_kb_embedding_dim(self, db_path: str) -> int:
        """获取知识库嵌入维度"""
        try:
            # 简化实现：从知识库信息文件读取
            kb_info_file = os.path.join(db_path, "kb_info.json")
            if os.path.exists(kb_info_file):
                import json
                with open(kb_info_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                    return info.get('embedding_dim', 1024)
            return 1024  # 默认维度
        except:
            return 1024
