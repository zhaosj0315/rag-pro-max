"""
应用主入口模块
负责协调所有模块，提供简化的主应用入口
"""

import streamlit as st
from src.core.environment import initialize_environment
from src.ui.page_style import PageStyle
from src.ui.sidebar_config import SidebarConfig
from src.core.main_controller import MainController
from src.core.app_config import load_config, get_existing_kbs
from src.utils.app_utils import initialize_session_state, show_first_time_guide, handle_kb_switching
from src.ui.message_renderer import MessageRenderer
from src.summary.auto_summary import AutoSummaryGenerator
from src.queue.queue_manager import QueueManager
from src.logging import LogManager

logger = LogManager()

class RAGProMaxApp:
    """RAG Pro Max 主应用类"""
    
    def __init__(self):
        # 初始化环境
        initialize_environment()
        
        # 设置页面
        PageStyle.setup_page()
        
        # 初始化状态
        initialize_session_state()
        
        # 加载配置
        self.defaults = load_config()
        self.output_base = "vector_db_storage"
        self.existing_kbs = get_existing_kbs(self.output_base)
        
        # 初始化控制器
        self.main_controller = MainController(self.output_base)
        self.queue_manager = QueueManager()
        
        # 性能监控（模拟）
        self.perf_monitor = type('PerfMonitor', (), {'render_panel': lambda: None})()
    
    def run(self):
        """运行主应用"""
        st.title("🛡️ RAG Pro Max")
        
        # 首次使用引导
        show_first_time_guide(self.existing_kbs)
        
        # 渲染侧边栏
        config_values, advanced_config = SidebarConfig.render_sidebar(self.defaults, self.perf_monitor)
        
        # 提取配置值
        config = SidebarConfig.extract_config_values(config_values)
        
        # 获取当前知识库
        current_kb_name = self._get_current_kb_name()
        active_kb_name = current_kb_name if current_kb_name != "创建新知识库" else None
        
        # 处理知识库切换
        if handle_kb_switching(active_kb_name, st.session_state.current_kb_id):
            # 处理知识库加载
            if self.main_controller.handle_kb_loading(
                active_kb_name, config['embed_provider'], config['embed_model'], 
                config['embed_key'], config['embed_url']
            ):
                # 处理自动摘要
                self.main_controller.handle_auto_summary(active_kb_name)
                
                # 渲染消息
                self.main_controller.handle_message_rendering(active_kb_name)
                
                # 处理用户输入
                user_input = st.chat_input("输入问题...")
                self.main_controller.handle_user_input(user_input)
                
                # 处理队列
                self.main_controller.handle_queue_processing(
                    active_kb_name, config['embed_provider'], config['embed_model'],
                    config['embed_key'], config['embed_url'], config['llm_model']
                )
        
        # 处理创建新知识库的情况
        if current_kb_name == "创建新知识库":
            PageStyle.render_welcome_message()
    
    def _get_current_kb_name(self):
        """获取当前选中的知识库名称"""
        # 这里需要从侧边栏获取选中的知识库
        # 简化版本，实际需要从 session_state 获取
        return st.session_state.get('current_nav', '创建新知识库').replace('📂 ', '')

def main():
    """主函数"""
    app = RAGProMaxApp()
    app.run()

if __name__ == "__main__":
    main()
