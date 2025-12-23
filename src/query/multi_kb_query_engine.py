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
            logger.warning("❌ 多知识库查询: 未选择任何知识库")
            return "❌ 未选择任何知识库"
        
        logger.info(f"🔍 开始多知识库联合查询: {len(kb_names)} 个知识库")
        logger.info(f"📋 知识库列表: {', '.join(kb_names)}")
        logger.info(f"❓ 查询问题: {question[:100]}{'...' if len(question) > 100 else ''}")
        
        # 并行查询所有知识库
        results = []
        with ThreadPoolExecutor(max_workers=min(len(kb_names), 4)) as executor:
            logger.info(f"⚡ 启动并行查询，最大并发数: {min(len(kb_names), 4)}")
            
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
                        logger.success(f"✅ [{completed_count}/{len(kb_names)}] {kb_name}: 查询成功")
                        results.append({
                            'kb_name': kb_name,
                            'content': result
                        })
                    else:
                        logger.warning(f"⚠️ [{completed_count}/{len(kb_names)}] {kb_name}: 返回空结果")
                except Exception as e:
                    logger.error(f"❌ [{completed_count}/{len(kb_names)}] {kb_name}: 查询失败 - {str(e)}")
                    results.append({
                        'kb_name': kb_name,
                        'content': f"查询失败: {str(e)}"
                    })
        
        # 整合答案
        logger.info("🔄 开始整合查询结果...")
        integrated_result = self._integrate_results(question, results)
        logger.success("✅ 多知识库联合查询完成")
        return integrated_result
    
    def _query_single_kb(self, question: str, kb_name: str, embed_provider: str,
                        embed_model: str, embed_key: str, embed_url: str) -> str:
        """查询单个知识库"""
        try:
            logger.info(f"🔍 开始查询知识库: {kb_name}")
            
            db_path = os.path.join(self.output_base, kb_name)
            if not os.path.exists(db_path):
                logger.error(f"❌ 知识库路径不存在: {db_path}")
                return f"知识库 {kb_name} 不存在"
            
            # 加载知识库
            logger.info(f"📂 加载知识库索引: {kb_name}")
            storage_context = StorageContext.from_defaults(persist_dir=db_path)
            index = load_index_from_storage(storage_context)
            
            # 创建查询引擎 - 优化参数提高答案质量
            logger.info(f"⚙️ 创建查询引擎: {kb_name}")
            query_engine = index.as_query_engine(
                similarity_top_k=5,
                response_mode="tree_summarize"
            )
            
            # 执行查询
            logger.info(f"🚀 执行查询: {kb_name}")
            response = query_engine.query(question)
            result = str(response)
            
            logger.info(f"📝 查询结果长度: {len(result)} 字符")
            return result
            
        except Exception as e:
            logger.error(f"❌ 查询知识库 {kb_name} 异常: {str(e)}")
            return f"查询知识库 {kb_name} 时出错: {str(e)}"
    
    def _integrate_results(self, question: str, results: List[dict]) -> str:
        """整合多个知识库的查询结果"""
        if not results:
            logger.warning("❌ 所有知识库查询均失败")
            return "❌ 所有知识库查询均失败"
        
        # 过滤有效结果 - 排除过于简短或无关的回答
        valid_results = []
        for r in results:
            content = r['content'].strip()
            # 过滤掉明显的错误、过短或无关回答
            if (not content.startswith('查询') and 
                len(content) > 10 and 
                not content.lower() in ['好的', '收到', '测试成功', '没有相关信息']):
                valid_results.append(r)
        
        logger.info(f"📊 结果统计: 总计 {len(results)} 个，有效 {len(valid_results)} 个")
        
        if not valid_results:
            # 所有查询都失败，返回错误信息
            logger.warning("⚠️ 没有有效的查询结果")
            error_summary = "\n".join([f"• {r['kb_name']}: {r['content']}" for r in results])
            return f"❌ 查询失败:\n{error_summary}"
        
        # 构建整合答案
        logger.info("🔧 构建整合答案...")
        answer_parts = []
        answer_parts.append(f"🔍 **基于 {len(valid_results)} 个知识库的联合查询结果:**\n")
        
        for i, result in enumerate(valid_results, 1):
            kb_name = result['kb_name']
            content = result['content'].strip()
            
            # 简化知识库名称显示
            display_name = kb_name.replace('_20251223_', ' ').replace('_', ' ')
            logger.info(f"📚 整合来源 {i}: {display_name} ({len(content)} 字符)")
            
            answer_parts.append(f"**📚 来源 {i}: {display_name}**")
            answer_parts.append(content)
            answer_parts.append("")  # 空行分隔
        
        # 如果有失败的查询，在末尾提及
        failed_results = [r for r in results if r['content'].startswith('查询')]
        if failed_results:
            logger.warning(f"⚠️ {len(failed_results)} 个知识库查询失败")
            answer_parts.append("⚠️ **部分知识库查询失败:**")
            for r in failed_results:
                answer_parts.append(f"• {r['kb_name']}: {r['content']}")
        
        final_answer = "\n".join(answer_parts)
        logger.success(f"✅ 答案整合完成，总长度: {len(final_answer)} 字符")
        return final_answer
