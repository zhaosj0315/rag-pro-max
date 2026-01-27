"""
知识库处理器 - 负责知识库的创建和处理逻辑
"""

import os
import time
import streamlit as st
from datetime import datetime


class KBProcessor:
    """知识库处理器"""
    
    def __init__(self):
        """初始化处理器"""
    
    def process_knowledge_base(self, kb_name: str, source_path: str, options: dict):
        """处理知识库创建逻辑"""
        from src.app_logging import LogManager
        logger = LogManager()
        
        # 获取输出路径
        output_base = os.path.join(os.getcwd(), "vector_db_storage")
        persist_dir = os.path.join(output_base, kb_name)
        start_time = time.time()
        
        # 资源保护检查
        import psutil
        from src.utils.adaptive_throttling import get_resource_guard
        
        resource_guard = get_resource_guard()
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
        result = resource_guard.check_resources(cpu, mem, 0)
        throttle_info = result.get('throttle', {})
        
        if throttle_info.get('action') == 'reject':
            st.warning(f"⚠️ 系统资源紧张，请稍后再试")
            logger.warning(f"资源不足，暂停处理: CPU={cpu}%, MEM={mem}%")
            return False
        
        # 设置嵌入模型
        embed_provider = options.get('embed_provider', 'HuggingFace (本地/极速)')
        embed_model = options.get('embed_model', 'sentence-transformers/all-MiniLM-L6-v2')
        embed_key = options.get('embed_key', '')
        embed_url = options.get('embed_url', '')
        
        logger.info(f"🔧 设置嵌入模型: {embed_model} (provider: {embed_provider})")
        
        from src.utils.model_manager import load_embedding_model
        embed = load_embedding_model(embed_provider, embed_model, embed_key, embed_url)
        
        if not embed:
            logger.error(f"❌ 嵌入模型加载失败: {embed_model}")
            st.error(f"无法加载嵌入模型: {embed_model}")
            return False
        
        from llama_index.core import Settings
        Settings.embed_model = embed
        
        try:
            actual_dim = len(embed._get_text_embedding("test"))
            logger.success(f"✅ 嵌入模型已设置: {embed_model} ({actual_dim}维)")
        except:
            logger.success(f"✅ 嵌入模型已设置: {embed_model}")
        
        # 注入日志样式优化 (v2.0)
        st.markdown("""
        <style>
        /* 优化 Status 容器内的日志显示 */
        div[data-testid="stStatusWidget"] div[data-testid="stMarkdown"] p {
            font-family: 'SF Mono', 'Segoe UI Mono', 'Roboto Mono', monospace;
            font-size: 0.85rem;
            white-space: pre-wrap !important;
            word-break: break-word !important; 
            line-height: 1.6;
            margin-bottom: 0px;
        }
        /* 滚动容器优化 */
        div[data-testid="stStatusWidget"] details > div {
            max-height: 500px;
            overflow-y: auto !important;
            background-color: #fafafa;
            border: 1px solid #eee;
            border-radius: 6px;
            padding: 12px;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.02);
        }
        /* 滚动条美化 */
        div[data-testid="stStatusWidget"] details > div::-webkit-scrollbar {
            width: 6px;
        }
        div[data-testid="stStatusWidget"] details > div::-webkit-scrollbar-thumb {
            background-color: #ddd;
            border-radius: 3px;
        }
        </style>
        """, unsafe_allow_html=True)

        logger.log("INFO", f"开始处理知识库: {kb_name}", stage="知识库处理")
        
        # UI 状态容器
        status_container = st.status(f"🚀 处理知识库: {kb_name}", expanded=True)
        prog_bar = status_container.progress(0)
        status_container.write(f"⏱️ 开始时间: {datetime.now().strftime('%H:%M:%S')}")
        
        # 回调函数：更新 UI (v2.0 结构化HTML)
        def status_callback(msg_type, *args):
            if msg_type == "step":
                step_num, step_desc = args
                # 步骤: 蓝色轻背景，强视觉引导
                html = f"""
                <div style="background-color: #e3f2fd; padding: 5px 10px; border-radius: 4px; border-left: 3px solid #2196f3; margin: 10px 0 5px 0;">
                    <span style="font-weight: 600; color: #0d47a1;">📂 步骤 {step_num}/6:</span> 
                    <span style="color: #1565c0;">{step_desc}</span>
                </div>
                """
                status_container.markdown(html, unsafe_allow_html=True)
                logger.info(f"📂 [步骤 {step_num}/6] {step_desc}")
                prog_bar.progress(step_num * 15)
                
            elif msg_type == "info":
                info_msg = args[0]
                # 信息: 增加左边距，区分层级
                icon = "🔹" if any(k in info_msg for k in ["正在", "开始"]) else "ℹ️"
                color = "#2e7d32" if "✅" in info_msg else "#444"
                
                html = f"""<div style="margin-left: 8px; color: {color}; line-height: 1.5;">{icon} {info_msg}</div>"""
                status_container.markdown(html, unsafe_allow_html=True)
                logger.info(f"   {info_msg}")
                
            elif msg_type == "warning":
                warn_msg = args[0]
                # 警告: 橙色轻背景
                html = f"""
                <div style="background-color: #fff3e0; padding: 4px 8px; border-radius: 4px; border-left: 3px solid #ff9800; margin: 4px 0;">
                    <span style="font-weight: 600; color: #e65100;">⚠️ 警告:</span> 
                    <span style="color: #ef6c00;">{warn_msg}</span>
                </div>
                """
                status_container.markdown(html, unsafe_allow_html=True)
                logger.warning(f"   ⚠️  {warn_msg}")
        
        # 验证源路径
        if not source_path or not os.path.exists(source_path):
            status_container.update(label="❌ 路径无效", state="error")
            logger.error(f"❌ 路径无效: {source_path}")
            st.error(f"路径无效: {source_path}")
            return False
        
        # 使用 IndexBuilder 构建索引
        try:
            from src.processors import IndexBuilder
            
            builder = IndexBuilder(
                kb_name=kb_name,
                persist_dir=persist_dir,
                embed_model=embed,
                embed_model_name=embed_model,
                extract_metadata=options.get('extract_metadata', False),
                generate_summary=options.get('generate_summary', False),
                logger=logger
            )
            
            result = builder.build(
                source_path=source_path,
                force_reindex=options.get('force_reindex', False),
                action_mode=options.get('action_mode', 'NEW'),
                status_callback=status_callback
            )
            
            if not result.success:
                status_container.update(label=f"❌ 处理失败: {result.error}", state="error")
                logger.error(f"❌ 处理失败: {result.error}")
                st.error(result.error)
                return False
            
            # 保存索引
            if result.index:
                result.index.storage_context.persist(persist_dir=persist_dir)
                logger.success(f"💾 索引已保存到: {persist_dir}")
            
            # 更新进度
            prog_bar.progress(100)
            
            # 计算耗时
            duration = time.time() - start_time
            logger.separator("处理完成")
            logger.success(f"✅ 知识库 '{kb_name}' 处理完成")
            logger.info(f"📊 统计: {result.file_count} 个文件, {result.doc_count} 个文档片段")
            logger.info(f"⏱️  耗时: {duration:.1f} 秒")
            
            logger.log("SUCCESS", f"知识库处理完成: {kb_name}, 文档数: {result.doc_count}", stage="知识库处理")
            
            status_container.update(label=f"✅ 知识库 '{kb_name}' 处理完成", state="complete", expanded=True)
            
            # 资源清理
            resource_guard.throttler.cleanup_memory()
            logger.info("🧹 资源已清理")
            
            return True
            
        except Exception as e:
            status_container.update(label=f"❌ 处理失败: {str(e)}", state="error")
            logger.error(f"❌ 处理失败: {str(e)}")
            st.error(f"处理失败: {str(e)}")
            return False
