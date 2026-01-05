from src.app_logging.log_manager import LogManager

logger = LogManager()

"""
应用初始化器 - 负责环境配置和应用启动
"""

import os
import warnings
import streamlit as st


class AppInitializer:
    """应用初始化管理器"""
    
    @staticmethod
    def setup_environment():
        """设置环境变量"""
        # 减少启动警告
        os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
        
        # 禁用PaddleOCR详细日志
        os.environ['GLOG_minloglevel'] = '3'
        os.environ['FLAGS_logtostderr'] = '0'
        os.environ['PADDLE_LOG_LEVEL'] = '50'
        os.environ['FLAGS_v'] = '0'
        os.environ['GLOG_v'] = '0'
        
        # 设置多进程相关环境变量
        os.environ['OMP_NUM_THREADS'] = '1'
        os.environ['MKL_NUM_THREADS'] = '1'
        os.environ['OPENBLAS_NUM_THREADS'] = '1'
        os.environ['VECLIB_MAXIMUM_THREADS'] = '1'
        
        # 抑制Pydantic警告
        warnings.filterwarnings("ignore", message=".*UnsupportedFieldAttributeWarning.*")
    
    @staticmethod
    def setup_streamlit():
        """配置Streamlit页面"""
        st.set_page_config(
            page_title="RAG Pro Max",
            page_icon="🚀",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    @staticmethod
    def setup_css():
        """注入CSS样式"""
        st.markdown("""
        <style>
        /* 修复统计卡片显示 */
        [data-testid="metric-container"] {
            background: rgba(248, 249, 251, 0.8) !important;
            border: 1px solid rgba(0, 0, 0, 0.08) !important;
            border-radius: 8px !important;
            padding: 0.75rem !important;
            margin: 0.25rem !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
            transition: all 0.2s ease !important;
            min-height: 80px !important;
        }
        
        [data-testid="metric-container"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
        }
        
        /* 侧边栏优化 */
        section[data-testid="stSidebar"] {
            min-width: 850px !important;
            width: 850px !important;
        }
        
        /* 紧凑布局 */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
        }
        </style>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def cleanup_temp_files():
        """清理超过24小时的临时文件"""
        from src.common.utils import cleanup_temp_files
        cleaned_count = cleanup_temp_files("temp_uploads", 24)
        if cleaned_count > 0:
            logger.info(f"🧹 已清理 {cleaned_count} 个临时文件")
    
    @staticmethod
    def initialize_app():
        """完整的应用初始化"""
        AppInitializer.setup_environment()
        AppInitializer.setup_streamlit()
        AppInitializer.setup_css()
        
        # 执行启动清理
        AppInitializer.cleanup_temp_files()
        
        # 初始化核心环境
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        from src.core.environment import initialize_environment
        initialize_environment()
