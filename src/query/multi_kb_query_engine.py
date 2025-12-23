"""
多知识库联合查询引擎
支持从多个知识库中并行检索并整合答案
"""

import os
import json
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from llama_index.core import StorageContext, load_index_from_storage

# 导入日志系统
from src.logger import logger


class MultiKBQueryEngine:
    """多知识库联合查询引擎"""
    
    def __init__(self, output_base: str):
        self.output_base = output_base
    
    def query(self, question: str, kb_names: List[str], embed_provider: str, 
              embed_model: str, embed_key: str, embed_url: str) -> str:
        """
        从多个知识库中查询并整合答案
        
        Args:
            question: 用户问题
            kb_names: 知识库名称列表
            embed_provider: 嵌入模型提供商
            embed_model: 嵌入模型名称
            embed_key: API密钥
            embed_url: API地址
            
        Returns:
            整合后的答案
        """
        if not kb_names:
            logger.log("多知识库查询", "error", "❌ 多知识库查询: 未选择任何知识库")
            return "❌ 未选择任何知识库"
        
        logger.log("多知识库查询", "start", f"🔍 联合查询开始: {len(kb_names)} 个知识库")
        
        # 并行查询所有知识库
        results = []
        with ThreadPoolExecutor(max_workers=min(len(kb_names), 4)) as executor:
            future_to_kb = {
                executor.submit(self._query_single_kb, question, kb_name, 
                              embed_provider, embed_model, embed_key, embed_url): kb_name
                for kb_name in kb_names
            }
            
            completed_count = 0
            for future in as_completed(future_to_kb):
                kb_name = future_to_kb[future]
                completed_count += 1
                try:
                    result = future.result()
                    if result and result.strip():
                        results.append({
                            'kb_name': kb_name,
                            'content': result
                        })
                    else:
                        logger.log("多知识库查询", "warning", f"⚠️ {kb_name}: 返回空结果")
                except Exception as e:
                    logger.log("多知识库查询", "error", f"❌ {kb_name}: {str(e)}")
                    results.append({
                        'kb_name': kb_name,
                        'content': f"查询失败: {str(e)}"
                    })
        
        # 整合答案
        integrated_result = self._integrate_results(question, results)
        logger.log("多知识库查询", "complete", f"✅ 联合查询完成: {len([r for r in results if not r['content'].startswith('查询')])} 个有效结果")
        return integrated_result
    
    def _query_single_kb(self, question: str, kb_name: str, embed_provider: str,
                        embed_model: str, embed_key: str, embed_url: str) -> str:
        """查询单个知识库"""
        try:
            db_path = os.path.join(self.output_base, kb_name)
            if not os.path.exists(db_path):
                return f"知识库 {kb_name} 不存在"
            
            # 加载知识库和创建查询引擎
            storage_context = StorageContext.from_defaults(persist_dir=db_path)
            index = load_index_from_storage(storage_context)
            query_engine = index.as_query_engine(
                similarity_top_k=5,
                response_mode="tree_summarize"
            )
            
            # 执行查询
            response = query_engine.query(question)
            return str(response)
            
        except Exception as e:
            return f"查询知识库 {kb_name} 时出错: {str(e)}"
    
    def _integrate_results(self, question: str, results: List[dict]) -> str:
        """整合多个知识库的查询结果"""
        if not results:
            return "❌ 所有知识库查询均失败"
        
        # 过滤有效结果
        valid_results = []
        for r in results:
            content = r['content'].strip()
            if (not content.startswith('查询') and 
                len(content) > 10 and 
                not content.lower() in ['好的', '收到', '测试成功', '没有相关信息']):
                valid_results.append(r)
        
        if not valid_results:
            error_summary = "\n".join([f"• {r['kb_name']}: {r['content']}" for r in results])
            return f"❌ 查询失败:\n{error_summary}"
        
        # 构建整合答案
        answer_parts = []
        answer_parts.append(f"🔍 **基于 {len(valid_results)} 个知识库的联合查询结果:**\n")
        
        for i, result in enumerate(valid_results, 1):
            kb_name = result['kb_name']
            content = result['content'].strip()
            
            # 简化知识库名称显示
            display_name = kb_name.replace('_20251223_', ' ').replace('_', ' ')
            
            answer_parts.append(f"**📚 来源 {i}: {display_name}**")
            answer_parts.append(content)
            answer_parts.append("")  # 空行分隔
        
        # 如果有失败的查询，在末尾提及
        failed_results = [r for r in results if r['content'].startswith('查询')]
        if failed_results:
            answer_parts.append("⚠️ **部分知识库查询失败:**")
            for r in failed_results:
                answer_parts.append(f"• {r['kb_name']}: {r['content']}")
        
        return "\n".join(answer_parts)
