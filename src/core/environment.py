"""
环境配置模块
负责环境变量设置、警告屏蔽和兼容性补丁
"""

import os
import sys
import warnings
import logging
import llama_index.core.schema as schema_module


def setup_environment():
    """设置环境配置"""
    # 设置离线模式
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'
    
    # 强制使用本地模型，避免 OpenAI 默认
    os.environ['LLAMA_INDEX_EMBED_MODEL'] = 'local'


def suppress_warnings():
    """屏蔽所有警告和日志"""
    # 屏蔽所有警告
    warnings.filterwarnings('ignore')
    
    # 设置环境变量抑制Streamlit文件监控
    os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"
    os.environ["STREAMLIT_SERVER_RUN_ON_SAVE"] = "false"
    
    # 屏蔽所有 Streamlit 相关日志
    for logger_name in ['streamlit', 'streamlit.runtime', 'streamlit.runtime.scriptrunner_utils', 
                       'streamlit.watcher', 'watchdog', 'tornado', 'asyncio']:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
        logging.getLogger(logger_name).propagate = False
    
    # 重定向 stderr 中的警告
    class SuppressWarnings:
        def write(self, text):
            if 'ScriptRunContext' not in text and 'WARNING' not in text:
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
