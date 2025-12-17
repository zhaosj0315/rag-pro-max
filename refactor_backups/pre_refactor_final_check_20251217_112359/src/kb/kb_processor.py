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
        pass
    
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
        embed_model = options.get('embed_model', 'BAAI/bge-small-zh-v1.5')
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
        
        logger.log("INFO", f"开始处理知识库: {kb_name}", stage="知识库处理")
        
        # UI 状态容器
        status_container = st.status(f"🚀 处理知识库: {kb_name}", expanded=True)
        prog_bar = status_container.progress(0)
        status_container.write(f"⏱️ 开始时间: {datetime.now().strftime('%H:%M:%S')}")
        
        # 回调函数：更新 UI
        def status_callback(msg_type, *args):
            if msg_type == "step":
                step_num, step_desc = args
                status_container.write(f"📂 [步骤{step_num}/6] {step_desc}")
                logger.info(f"📂 [步骤 {step_num}/6] {step_desc}")
                prog_bar.progress(step_num * 15)
            elif msg_type == "info":
                info_msg = args[0]
                status_container.write(f"   {info_msg}")
                logger.info(f"   {info_msg}")
            elif msg_type == "warning":
                warn_msg = args[0]
                status_container.write(f"   ⚠️  {warn_msg}")
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
