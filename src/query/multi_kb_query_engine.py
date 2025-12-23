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
        
        logger.log("多知识库查询", "start", f"🔍 开始多知识库联合查询")
        logger.log("多知识库查询", "info", f"📊 知识库数量: {len(kb_names)} 个")
        logger.log("多知识库查询", "info", f"📋 知识库列表: {', '.join(kb_names)}")
        logger.log("多知识库查询", "info", f"❓ 查询问题: {question}")
        logger.log("多知识库查询", "info", f"📏 问题长度: {len(question)} 字符")
        logger.log("多知识库查询", "info", f"🔧 嵌入模型: {embed_provider}/{embed_model}")
        
        # 并行查询所有知识库
        results = []
        max_workers = min(len(kb_names), 4)
        logger.log("多知识库查询", "info", f"⚡ 启动并行查询")
        logger.log("多知识库查询", "info", f"🔢 最大并发数: {max_workers}")
        logger.log("多知识库查询", "info", f"🧵 使用 ThreadPoolExecutor")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            logger.log("多知识库查询", "info", f"📤 提交 {len(kb_names)} 个查询任务")
            
            future_to_kb = {
                executor.submit(self._query_single_kb, question, kb_name, 
                              embed_provider, embed_model, embed_key, embed_url): kb_name
                for kb_name in kb_names
            }
            
            completed_count = 0
            for future in as_completed(future_to_kb):
                kb_name = future_to_kb[future]
                completed_count += 1
                logger.log("多知识库查询", "info", f"📥 收到查询结果 [{completed_count}/{len(kb_names)}]: {kb_name}")
                
                try:
                    result = future.result()
                    if result and result.strip():
                        logger.log("多知识库查询", "success", f"✅ [{completed_count}/{len(kb_names)}] {kb_name}: 查询成功")
                        logger.log("多知识库查询", "info", f"📝 结果长度: {len(result)} 字符")
                        results.append({
                            'kb_name': kb_name,
                            'content': result
                        })
                    else:
                        logger.log("多知识库查询", "warning", f"⚠️ [{completed_count}/{len(kb_names)}] {kb_name}: 返回空结果")
                except Exception as e:
                    logger.log("多知识库查询", "error", f"❌ [{completed_count}/{len(kb_names)}] {kb_name}: 查询失败")
                    logger.log("多知识库查询", "error", f"🔍 错误详情: {str(e)}")
                    results.append({
                        'kb_name': kb_name,
                        'content': f"查询失败: {str(e)}"
                    })
        
        logger.log("多知识库查询", "info", f"📊 并行查询完成，收集到 {len(results)} 个结果")
        
        # 整合答案
        logger.log("多知识库查询", "info", "🔄 开始整合查询结果...")
        integrated_result = self._integrate_results(question, results)
        logger.log("多知识库查询", "complete", f"✅ 多知识库联合查询完成")
        logger.log("多知识库查询", "info", f"📄 最终答案长度: {len(integrated_result)} 字符")
        return integrated_result
    
    def _query_single_kb(self, question: str, kb_name: str, embed_provider: str,
                        embed_model: str, embed_key: str, embed_url: str) -> str:
        """查询单个知识库"""
        try:
            logger.log("单知识库查询", "start", f"🔍 开始查询知识库: {kb_name}")
            
            db_path = os.path.join(self.output_base, kb_name)
            logger.log("单知识库查询", "info", f"📁 知识库路径: {db_path}")
            
            if not os.path.exists(db_path):
                logger.log("单知识库查询", "error", f"❌ 知识库路径不存在: {db_path}")
                return f"知识库 {kb_name} 不存在"
            
            # 检查知识库文件
            docstore_path = os.path.join(db_path, "docstore.json")
            index_store_path = os.path.join(db_path, "index_store.json")
            logger.log("单知识库查询", "info", f"📄 检查文件: docstore.json {'✓' if os.path.exists(docstore_path) else '✗'}")
            logger.log("单知识库查询", "info", f"📄 检查文件: index_store.json {'✓' if os.path.exists(index_store_path) else '✗'}")
            
            # 加载知识库
            logger.log("单知识库查询", "loading", f"📂 加载知识库索引: {kb_name}")
            storage_context = StorageContext.from_defaults(persist_dir=db_path)
            index = load_index_from_storage(storage_context)
            logger.log("单知识库查询", "success", f"✅ 索引加载成功: {kb_name}")
            
            # 创建查询引擎
            logger.log("单知识库查询", "info", f"⚙️ 创建查询引擎: {kb_name}")
            logger.log("单知识库查询", "info", f"🔧 查询参数: similarity_top_k=5, response_mode=tree_summarize")
            query_engine = index.as_query_engine(
                similarity_top_k=5,
                response_mode="tree_summarize"
            )
            logger.log("单知识库查询", "success", f"✅ 查询引擎创建成功: {kb_name}")
            
            # 执行查询
            logger.log("单知识库查询", "processing", f"🚀 执行查询: {kb_name}")
            logger.log("单知识库查询", "info", f"❓ 查询内容: {question[:50]}{'...' if len(question) > 50 else ''}")
            response = query_engine.query(question)
            result = str(response)
            
            logger.log("单知识库查询", "complete", f"✅ {kb_name} 查询完成")
            logger.log("单知识库查询", "info", f"📝 结果长度: {len(result)} 字符")
            logger.log("单知识库查询", "info", f"📄 结果预览: {result[:100]}{'...' if len(result) > 100 else ''}")
            return result
            
        except Exception as e:
            logger.log("单知识库查询", "error", f"❌ 查询知识库 {kb_name} 异常: {str(e)}")
            logger.log("单知识库查询", "error", f"🔍 异常类型: {type(e).__name__}")
            return f"查询知识库 {kb_name} 时出错: {str(e)}"
    
    def _integrate_results(self, question: str, results: List[dict]) -> str:
        """整合多个知识库的查询结果"""
        logger.log("结果整合", "start", "🔄 开始结果整合处理")
        
        if not results:
            logger.log("结果整合", "error", "❌ 所有知识库查询均失败")
            return "❌ 所有知识库查询均失败"
        
        # 过滤有效结果
        logger.log("结果整合", "info", f"📊 开始结果过滤，原始结果数: {len(results)}")
        valid_results = []
        filtered_count = 0
        
        for i, r in enumerate(results, 1):
            content = r['content'].strip()
            kb_name = r['kb_name']
            
            logger.log("结果整合", "info", f"🔍 检查结果 {i}: {kb_name}")
            logger.log("结果整合", "info", f"📏 内容长度: {len(content)} 字符")
            
            # 详细的过滤逻辑
            if content.startswith('查询'):
                logger.log("结果整合", "warning", f"⚠️ 过滤: {kb_name} - 查询失败")
                filtered_count += 1
            elif len(content) <= 10:
                logger.log("结果整合", "warning", f"⚠️ 过滤: {kb_name} - 内容过短 ({len(content)} 字符)")
                filtered_count += 1
            elif content.lower() in ['好的', '收到', '测试成功', '没有相关信息']:
                logger.log("结果整合", "warning", f"⚠️ 过滤: {kb_name} - 无关回答")
                filtered_count += 1
            else:
                logger.log("结果整合", "success", f"✅ 有效结果: {kb_name}")
                valid_results.append(r)
        
        logger.log("结果整合", "info", f"📊 过滤统计: 总计 {len(results)} 个，有效 {len(valid_results)} 个，过滤 {filtered_count} 个")
        
        if not valid_results:
            logger.log("结果整合", "warning", "⚠️ 没有有效的查询结果")
            error_summary = "\n".join([f"• {r['kb_name']}: {r['content']}" for r in results])
            return f"❌ 查询失败:\n{error_summary}"
        
        # 构建整合答案
        logger.log("结果整合", "processing", "🔧 开始构建整合答案...")
        answer_parts = []
        answer_parts.append(f"🔍 **基于 {len(valid_results)} 个知识库的联合查询结果:**\n")
        
        total_content_length = 0
        for i, result in enumerate(valid_results, 1):
            kb_name = result['kb_name']
            content = result['content'].strip()
            total_content_length += len(content)
            
            # 简化知识库名称显示
            display_name = kb_name.replace('_20251223_', ' ').replace('_', ' ')
            logger.log("结果整合", "info", f"📚 整合来源 {i}: {display_name}")
            logger.log("结果整合", "info", f"📄 来源内容长度: {len(content)} 字符")
            logger.log("结果整合", "info", f"📝 内容预览: {content[:80]}{'...' if len(content) > 80 else ''}")
            
            answer_parts.append(f"**📚 来源 {i}: {display_name}**")
            answer_parts.append(content)
            answer_parts.append("")  # 空行分隔
        
        # 如果有失败的查询，在末尾提及
        failed_results = [r for r in results if r['content'].startswith('查询')]
        if failed_results:
            logger.log("结果整合", "warning", f"⚠️ {len(failed_results)} 个知识库查询失败")
            logger.log("结果整合", "info", f"❌ 失败列表: {[r['kb_name'] for r in failed_results]}")
            answer_parts.append("⚠️ **部分知识库查询失败:**")
            for r in failed_results:
                answer_parts.append(f"• {r['kb_name']}: {r['content']}")
        
        final_answer = "\n".join(answer_parts)
        logger.log("结果整合", "complete", f"✅ 答案整合完成")
        logger.log("结果整合", "info", f"📄 最终答案长度: {len(final_answer)} 字符")
        logger.log("结果整合", "info", f"📊 内容统计: {len(valid_results)} 个来源，总内容 {total_content_length} 字符")
        logger.log("结果整合", "info", f"📝 答案预览: {final_answer[:150]}{'...' if len(final_answer) > 150 else ''}")
        
        return final_answer
