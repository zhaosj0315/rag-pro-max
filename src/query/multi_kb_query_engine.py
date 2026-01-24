#!/usr/bin/env python3
"""
多知识库联合问答系统 - 多进程优化版
支持同时查询多个知识库并整合结果，使用多进程避免GIL限制
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
import multiprocessing as mp
from pathlib import Path

def query_single_kb_worker(kb_name: str, query: str, top_k: int = 3) -> Dict[str, Any]:
    """
    单个知识库查询工作函数 - 用于多进程
    必须是顶级函数才能被pickle序列化
    """
    try:
        # 在子进程中导入，避免序列化问题
        import sys
        import os
        
        # 添加项目路径
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from src.rag_engine import create_rag_engine
        
        # 创建查询引擎
        rag_engine = create_rag_engine(kb_name)
        if not rag_engine:
            return {
                "kb_name": kb_name,
                "success": False,
                "error": "无法创建查询引擎",
                "results": []
            }
        
        # 执行查询
        query_engine = rag_engine.get_query_engine()
        response = query_engine.query(query)
        
        # 提取源文档信息
        source_nodes = getattr(response, 'source_nodes', [])
        results = []
        
        for node in source_nodes[:top_k]:
            results.append({
                "content": node.text[:500] + "..." if len(node.text) > 500 else node.text,
                "score": getattr(node, 'score', 0.0),
                "metadata": getattr(node, 'metadata', {}),
                "source": getattr(node.metadata, 'file_name', 'Unknown') if hasattr(node, 'metadata') else 'Unknown'
            })
        
        return {
            "kb_name": kb_name,
            "success": True,
            "answer": str(response),
            "results": results,
            "query_time": time.time()
        }
        
    except Exception as e:
        return {
            "kb_name": kb_name,
            "success": False,
            "error": str(e),
            "results": []
        }

class MultiKBQueryEngine:
    """多知识库联合查询引擎 - 多进程优化版"""
    
    def __init__(self):
        self.base_path = "vector_db_storage"
        # 获取CPU核心数，但限制最大进程数
        self.max_workers = min(mp.cpu_count(), 4)
    
    def get_available_kbs(self) -> List[str]:
        """获取可用的知识库列表"""
        try:
            base_dir = Path(self.base_path)
            if not base_dir.exists():
                return []
            
            kbs = []
            for item in base_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # 检查是否有索引文件
                    if (item / "docstore.json").exists() or (item / "index_store.json").exists():
                        kbs.append(item.name)
            
            return sorted(kbs)
        except Exception:
            return []
    
    def query_multiple_kbs(self, kb_names: List[str], query: str, 
                          top_k_per_kb: int = 3, max_workers: Optional[int] = None) -> Dict[str, Any]:
        """并行查询多个知识库 - 使用多进程"""
        if not kb_names:
            return {"success": False, "error": "未选择知识库"}
        
        start_time = time.time()
        results = {}
        
        # 确定进程数
        if max_workers is None:
            max_workers = min(self.max_workers, len(kb_names))
        else:
            max_workers = min(max_workers, len(kb_names), self.max_workers)
        
        try:
            # 使用多进程池
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                # 提交查询任务
                future_to_kb = {
                    executor.submit(query_single_kb_worker, kb_name, query, top_k_per_kb): kb_name 
                    for kb_name in kb_names
                }
                
                # 收集结果
                for future in as_completed(future_to_kb, timeout=60):  # 总超时60秒
                    kb_name = future_to_kb[future]
                    try:
                        result = future.result(timeout=30)  # 单个任务30秒超时
                        results[kb_name] = result
                    except Exception as e:
                        results[kb_name] = {
                            "kb_name": kb_name,
                            "success": False,
                            "error": f"查询超时或失败: {str(e)}",
                            "results": []
                        }
        
        except Exception as e:
            # 如果多进程失败，回退到单线程模式
            st.warning("⚠️ 多进程查询失败，回退到单线程模式")
            for kb_name in kb_names:
                try:
                    result = self._query_single_kb_fallback(kb_name, query, top_k_per_kb)
                    results[kb_name] = result
                except Exception as kb_error:
                    results[kb_name] = {
                        "kb_name": kb_name,
                        "success": False,
                        "error": f"查询失败: {str(kb_error)}",
                        "results": []
                    }
        
        # 整合结果
        total_time = time.time() - start_time
        successful_queries = [r for r in results.values() if r["success"]]
        
        return {
            "success": len(successful_queries) > 0,
            "query": query,
            "kb_count": len(kb_names),
            "successful_count": len(successful_queries),
            "total_time": total_time,
            "results": results,
            "used_multiprocessing": True
        }
    
    def _query_single_kb_fallback(self, kb_name: str, query: str, top_k: int = 3) -> Dict[str, Any]:
        """单线程回退查询方法"""
        try:
            from src.rag_engine import create_rag_engine
            
            rag_engine = create_rag_engine(kb_name)
            if not rag_engine:
                return {
                    "kb_name": kb_name,
                    "success": False,
                    "error": "无法创建查询引擎",
                    "results": []
                }
            
            query_engine = rag_engine.get_query_engine()
            response = query_engine.query(query)
            
            source_nodes = getattr(response, 'source_nodes', [])
            results = []
            
            for node in source_nodes[:top_k]:
                results.append({
                    "content": node.text[:500] + "..." if len(node.text) > 500 else node.text,
                    "score": getattr(node, 'score', 0.0),
                    "metadata": getattr(node, 'metadata', {}),
                    "source": getattr(node.metadata, 'file_name', 'Unknown') if hasattr(node, 'metadata') else 'Unknown'
                })
            
            return {
                "kb_name": kb_name,
                "success": True,
                "answer": str(response),
                "results": results,
                "query_time": time.time()
            }
            
        except Exception as e:
            return {
                "kb_name": kb_name,
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def generate_integrated_answer(self, multi_kb_results: Dict[str, Any]) -> str:
        """生成整合答案"""
        if not multi_kb_results["success"]:
            return "查询失败，请检查知识库状态。"
        
        successful_results = [r for r in multi_kb_results["results"].values() if r["success"]]
        
        if not successful_results:
            return "未找到相关信息。"
        
        # 构建整合答案
        integrated_answer = f"**基于 {len(successful_results)} 个知识库的查询结果：**\n\n"
        
        for i, result in enumerate(successful_results, 1):
            kb_name = result["kb_name"]
            answer = result.get("answer", "无答案")
            
            integrated_answer += f"### 📚 知识库 {i}: {kb_name}\n"
            integrated_answer += f"{answer}\n\n"
        
        # 添加统计信息
        integrated_answer += f"---\n"
        integrated_answer += f"**查询统计**: {multi_kb_results['successful_count']}/{multi_kb_results['kb_count']} 个知识库响应成功，"
        integrated_answer += f"耗时 {multi_kb_results['total_time']:.2f} 秒"
        
        # 添加性能信息
        if multi_kb_results.get("used_multiprocessing"):
            integrated_answer += f"，使用多进程加速"
        
        return integrated_answer

class MultiKBInterface:
    """多知识库问答界面"""
    
    def __init__(self):
        self.query_engine = MultiKBQueryEngine()
    
    def render_kb_selector(self) -> List[str]:
        """渲染知识库选择器"""
        available_kbs = self.query_engine.get_available_kbs()
        
        if not available_kbs:
            st.warning("📭 暂无可用知识库，请先创建知识库并上传文档。" )
            return []
        
        st.markdown("##### 📚 选择知识库")
        
        # 全选/全不选
        col1, col2 = st.columns([1, 4])
        with col1:
            select_all = st.checkbox("全选", key="select_all_kbs")
        
        # 知识库选择
        if select_all:
            selected_kbs = st.multiselect(
                "选择要查询的知识库（可多选）",
                available_kbs,
                default=available_kbs,
                key="selected_kbs"
            )
        else:
            selected_kbs = st.multiselect(
                "选择要查询的知识库（可多选）",
                available_kbs,
                key="selected_kbs"
            )
        
        # 显示选择统计
        if selected_kbs:
            st.info(f"✅ 已选择 {len(selected_kbs)} 个知识库: {', '.join(selected_kbs)}")
        
        return selected_kbs
    
    def render_query_options(self) -> Dict[str, Any]:
        """渲染查询选项"""
        with st.expander("🔧 查询设置", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                top_k_per_kb = st.slider(
                    "每个知识库返回结果数",
                    min_value=1,
                    max_value=10,
                    value=3,
                    key="top_k_per_kb"
                )
            
            with col2:
                max_workers = st.slider(
                    "并发进程数",
                    min_value=1,
                    max_value=min(mp.cpu_count(), 4),
                    value=min(mp.cpu_count(), 3),
                    key="max_workers",
                    help=f"当前系统有 {mp.cpu_count()} 个CPU核心"
                )
        
        return {
            "top_k_per_kb": top_k_per_kb,
            "max_workers": max_workers
        }
    
    def render_results(self, multi_kb_results: Dict[str, Any]):
        """渲染查询结果"""
        if not multi_kb_results["success"]:
            st.error("❌ 查询失败")
            return
        
        # 整合答案
        integrated_answer = self.query_engine.generate_integrated_answer(multi_kb_results)
        
        st.markdown("##### 🎯 整合答案")
        st.markdown(integrated_answer)
        
        # 详细结果
        with st.expander("📋 详细结果", expanded=False):
            for kb_name, result in multi_kb_results["results"].items():
                if result["success"]:
                    st.write(f"**📚 {kb_name}**")
                    
                    # 显示相关文档
                    if result["results"]:
                        for i, doc in enumerate(result["results"], 1):
                            with st.container(border=True):
                                st.write(f"**文档 {i}**: {doc['source']}")
                                st.write(f"**相关度**: {doc['score']:.3f}")
                                st.write(f"**内容**: {doc['content']}")
                    else:
                        st.info("未找到相关文档")
                else:
                    st.error(f"❌ {kb_name}: {result['error']}")
    
    def render_interface(self):
        """渲染完整界面"""
        st.title("🔍 多知识库联合问答")
        st.markdown("同时查询多个知识库，获得更全面的答案（多进程加速）")
        
        # 性能提示
        st.info(f"💡 系统检测到 {mp.cpu_count()} 个CPU核心，将使用多进程并行查询以获得最佳性能")
        
        # 知识库选择
        selected_kbs = self.render_kb_selector()
        
        if not selected_kbs:
            return
        
        # 查询选项
        query_options = self.render_query_options()
        
        # 查询输入
        st.markdown("##### 💬 提出问题")
        query = st.text_area(
            "请输入您的问题",
            placeholder="例如：什么是人工智能？",
            height=100,
            key="multi_kb_query"
        )
        
        # 查询按钮
        if st.button("🔍 开始查询", type="primary", disabled=not query.strip()):
            if query.strip():
                with st.spinner(f"正在使用 {query_options['max_workers']} 个进程并行查询 {len(selected_kbs)} 个知识库..."):
                    # 执行查询
                    results = self.query_engine.query_multiple_kbs(
                        selected_kbs,
                        query.strip(),
                        query_options["top_k_per_kb"],
                        query_options["max_workers"]
                    )
                    
                    # 显示结果
                    self.render_results(results)

# 全局实例
multi_kb_interface = MultiKBInterface()

def render_multi_kb_query():
    """渲染多知识库查询界面 - 便捷函数"""
    return multi_kb_interface.render_interface()