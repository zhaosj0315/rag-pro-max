"""
应用初始化器 - 负责环境配置和应用启动
"""

import os
import time
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
            min-width: 350px !important;
            width: 350px !important;
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
        temp_dir = "temp_uploads"
        if not os.path.exists(temp_dir):
            return
        
        # 安全检查：确保目录路径正确
        temp_dir = os.path.abspath(temp_dir)
        if not temp_dir.endswith("temp_uploads"):
            print("⚠️ 清理路径异常，跳过清理")
            return
        
        current_time = time.time()
        cleaned_count = 0
        
        try:
            for filename in os.listdir(temp_dir):
                # 跳过隐藏文件和系统文件
                if filename.startswith('.'):
                    continue
                    
                filepath = os.path.join(temp_dir, filename)
                
                # 安全检查：确保是文件且有读写权限
                if not os.path.isfile(filepath):
                    continue
                if not os.access(filepath, os.R_OK | os.W_OK):
                    continue
                    
                # 检查文件修改时间
                try:
                    file_time = os.path.getmtime(filepath)
                    # 如果文件超过24小时（86400秒）
                    if current_time - file_time > 86400:
                        os.remove(filepath)
                        cleaned_count += 1
                except (OSError, IOError) as e:
                    print(f"清理文件 {filename} 时出错: {e}")
                    continue
            
            if cleaned_count > 0:
                print(f"🧹 已清理 {cleaned_count} 个临时文件")
        except Exception as e:
            print(f"清理临时文件时出错: {e}")
    
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
        import time
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
        from src.core.environment import initialize_environment
        initialize_environment()
