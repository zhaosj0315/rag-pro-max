"""
环境配置模块
负责环境变量设置、警告屏蔽和兼容性补丁
"""

import os
import sys
import warnings
import logging  # 允许使用 - 环境配置专用
from src.app_logging.log_manager import LogManager
import llama_index.core.schema as schema_module


def setup_environment():
    """设置环境配置"""
    # 禁用模型源检查（减少启动日志）
    os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
    # 再次强制确认，防止部分库初始化过早读取
    if 'DISABLE_MODEL_SOURCE_CHECK' not in os.environ:
         os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
    
    # 设置离线模式
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    
    # 强制使用本地模型，避免 OpenAI 默认
    os.environ['LLAMA_INDEX_EMBED_MODEL'] = 'local'
    
    # 强制绕过代理（解决Surge等代理软件拦截本地请求的问题）
    os.environ['NO_PROXY'] = 'localhost,127.0.0.1,0.0.0.0'
    os.environ['no_proxy'] = 'localhost,127.0.0.1,0.0.0.0'


def suppress_warnings():
    """屏蔽所有警告和日志"""
    # 屏蔽所有警告
    warnings.filterwarnings('ignore')
    
    # 设置环境变量抑制Streamlit文件监控
    os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"
    os.environ["STREAMLIT_SERVER_RUN_ON_SAVE"] = "false"
    
    # 屏蔽所有 Streamlit 相关日志
    loggers_to_silence = [
        'streamlit', 
        'streamlit.runtime', 
        'streamlit.runtime.scriptrunner_utils',
        'streamlit.runtime.scriptrunner_utils.script_run_context',  # 明确指定该 Logger
        'streamlit.runtime.state.session_state_proxy',  # 屏蔽 Session State 警告
        'streamlit.watcher', 
        'watchdog', 
        'tornado', 
        'asyncio'
    ]
    
    for logger_name in loggers_to_silence:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.CRITICAL)  # 提升到 CRITICAL 级别
        logger.propagate = False
    
    # 重定向 stderr 中的警告
    class SuppressWarnings:
        def write(self, text):
            # 过滤不需要的日志关键词
            ignore_keywords = [
                'ScriptRunContext', 
                'WARNING', 
                'session_state_proxy',
                'Checking connectivity',
                'DISABLE_MODEL_SOURCE_CHECK'
            ]
            if not any(keyword in text for keyword in ignore_keywords):
                sys.__stderr__.write(text)
        def flush(self):
            sys.__stderr__.flush()
    
    sys.stderr = SuppressWarnings()


def apply_compatibility_patches():
    """应用兼容性补丁"""
    # LlamaIndex 版本兼容性补丁
    original_textnode = schema_module.TextNode
    
    class PatchedTextNode(original_textnode):
        def get_doc_id(self):
            return self.ref_doc_id or self.node_id
    
    schema_module.TextNode = PatchedTextNode


def initialize_environment():
    """初始化完整环境"""
    setup_environment()
    suppress_warnings()
    apply_compatibility_patches()
