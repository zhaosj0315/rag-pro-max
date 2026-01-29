"""
应用工具函数模块
负责应用级别的通用工具函数
"""

import os
import json
import time
import streamlit as st
from src.app_logging import LogManager

logger = LogManager()


def get_kb_embedding_dim(db_path):
    """检测知识库的向量维度 (Legacy: 仅返回维度)"""
    info = get_kb_model_info(db_path)
    return info.get('dim')

def get_kb_model_info(db_path):
    """获取知识库的模型信息 (名称和维度)"""
    result = {'name': None, 'dim': None}
    try:
        # 尝试读取 .kb_info.json
        kb_info_file = os.path.join(db_path, ".kb_info.json")
        if os.path.exists(kb_info_file):
            with open(kb_info_file, 'r') as f:
                kb_info = json.load(f)
                model = kb_info.get('embedding_model', '')
                result['name'] = model
                
                # 优先直接读取保存的维度
                if 'embedding_dim' in kb_info and isinstance(kb_info['embedding_dim'], int):
                    result['dim'] = kb_info['embedding_dim']
                    return result

                # 根据模型名推断维度
                if 'MiniLM' in model:
                    result['dim'] = 384
                elif 'small' in model:
                    result['dim'] = 512
                elif 'base' in model:
                    result['dim'] = 768
                elif 'm3' in model:
                    result['dim'] = 1024
        
        # 尝试从向量文件推断 (如果 json 读取失败或没有维度)
        if result['dim'] is None:
            import glob
            vector_files = glob.glob(os.path.join(db_path, "**/*.json"), recursive=True)
            if vector_files:
                # 简单启发式：根据文件大小推断
                total_size = sum(os.path.getsize(f) for f in vector_files) / (1024 * 1024)
                if total_size < 50:
                    result['dim'] = 512  # 小模型
                elif total_size < 200:
                    result['dim'] = 768  # 中模型
                else:
                    result['dim'] = 1024  # 大模型
    except:
        pass
    return result




def remove_file_from_manifest(db_path, filename):
    """从 manifest 中移除文件"""
    try:
        from src.config import ManifestManager
        
        manifest_path = ManifestManager.get_path(db_path)
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # 移除文件
            manifest['files'] = [f for f in manifest['files'] if f['name'] != filename]
            
            # 保存更新后的 manifest
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=4, ensure_ascii=False)
            
            logger.info(f"已从 manifest 中移除文件: {filename}")
            
    except Exception as e:
        logger.error(f"移除文件失败: {e}")


def initialize_session_state():
    """初始化 session state"""
    defaults = {
        "messages": [],
        "chat_engine": None,
        "prompt_trigger": None,
        "current_kb_id": None,
        "renaming": False,
        "suggestions_history": [],
        "is_processing": False,
        "quote_content": None,
        "first_time_guide_shown": False,
        "question_queue": [],
        "enable_query_optimization": False,
        "enable_web_search": False,
        "enable_deep_research": False,
        "last_search_results": None,
        "last_research_details": None,
        "last_optimized_query": None
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def show_first_time_guide(existing_kbs):
    """显示首次使用引导"""
    if not st.session_state.first_time_guide_shown and len(existing_kbs) == 0:
        st.info("""
        ### 👋 欢迎使用 RAG Pro Max！
        
        **快速开始指南：**
        
        1️⃣ **配置 LLM**（左侧边栏）
        - 选择 Ollama（本地）或 OpenAI（云端）
        - 输入相应的 API 信息
        
        2️⃣ **创建知识库**
        - 输入知识库名称
        - 选择文档路径或上传文件
        
        3️⃣ **开始对话**
        - 上传完成后即可开始提问
        - 支持多轮对话和引用回复
        
        💡 **提示**：首次使用建议点击"⚡ 一键配置"快速开始！
        """)
        
        if st.button("✅ 我知道了，开始使用", use_container_width=True):
            st.session_state.first_time_guide_shown = True
            st.rerun()


def open_file_native(file_path):
    """
    使用系统默认程序打开文件 (macOS 原生预览)
    
    Args:
        file_path: 文件路径
    """
    import platform
    import subprocess
    
    # 获取绝对路径并检查
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        logger.debug(abs_path)
        logger.error(f"文件不存在，无法打开: {abs_path}")
        return False
        
    try:
        system = platform.system()
        if system == "Darwin":  # macOS
            logger.debug(abs_path)
            # 方案 A: 尝试 Quick Look (qlmanage)
            try:
                # 1. 启动预览进程
                subprocess.Popen(
                    ["qlmanage", "-p", abs_path], 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
                
                # 2. 强制将预览窗口置于最前端
                # 给预览窗口一点点启动时间，然后使用 AppleScript 激活它
                time.sleep(0.3)
                subprocess.run([
                    "osascript", "-e", 
                    'tell application "System Events" to set frontmost of process "qlmanage" to true'
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                return True
            except Exception as e:
                logger.debug(e)
                # 方案 B: 退而求其次，使用系统默认关联程序打开 (Preview.app 等)
                subprocess.run(["open", abs_path])
                return True
                
        elif system == "Windows":
            logger.debug(abs_path)
            os.startfile(abs_path)
        else:  # Linux
            logger.debug(abs_path)
            subprocess.run(["xdg-open", abs_path])
        return True
    except Exception as e:
        logger.debug(e)
        logger.error(f"原生预览打开失败: {e}")
        return False


def handle_kb_switching(active_kb_name, current_kb_id):
    """处理知识库切换逻辑"""
    if active_kb_name and active_kb_name != current_kb_id:
        # 只在没有正在处理的问题时才切换
        if not st.session_state.get('is_processing', False):
            st.session_state.current_kb_id = active_kb_name
            st.session_state.chat_engine = None
            
            with st.spinner("📜 正在加载对话历史..."):
                from src.chat import HistoryManager
                st.session_state.messages = HistoryManager.load(active_kb_name)
            
            st.session_state.suggestions_history = []
            return True
        else:
            st.warning("⚠️ 正在处理问题，请等待完成后再切换知识库")
            st.session_state.current_nav = f"📂 {current_kb_id}"
            return False
    
    return True
