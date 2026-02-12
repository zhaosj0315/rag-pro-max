import streamlit as st
import os
import re

class TacticalDashboardAdapter:
    """
    Enhanced Adapter for integrating the external Tactical Dashboard.
    Performs code sanitization to prevent global style pollution and infinite reruns.
    """
    
    SOURCE_PATH = "/Users/zhaosj/.openclaw/workspace/dashboard/dashboard.py"

    @staticmethod
    def render():
        if not os.path.exists(TacticalDashboardAdapter.SOURCE_PATH):
            st.error(f"❌ 找不到战术仪表盘源文件: {TacticalDashboardAdapter.SOURCE_PATH}")
            return

        try:
            with open(TacticalDashboardAdapter.SOURCE_PATH, 'r', encoding='utf-8') as f:
                code = f.read()

            # --- 核心修复逻辑：源码级脱敏 ---
            
            # 1. 禁用全局页面配置
            code = re.sub(r'st\.set_page_config\(.*?\)', '# [Scoped] st.set_page_config disabled', code, flags=re.DOTALL)
            
            # 2. 移除全局背景和字体污染 (.stApp)
            # 我们将背景色改为仅针对仪表盘内部容器，或者干脆移除以适配 RAG Pro Max 主题
            code = code.replace('.stApp { background-color: #000000;', '/* .stApp style removed */ .dashboard-container { background-color: #000000;')
            
            # 3. 移除强制隐藏 Header/Footer (这会把 RAG Pro Max 的导航弄丢)
            code = code.replace('header, footer { visibility: hidden; }', '/* header/footer visibility preserved */')
            
            # 4. 禁用强制刷新 (st.rerun)
            # RAG Pro Max 管理后台不需要也不应该被外部脚本每 3 秒重刷一次
            code = code.replace('st.rerun()', '# [Scoped] st.rerun disabled')
            code = code.replace('time.sleep(3)', '# [Scoped] sleep disabled')

            # 5. 注入局部作用域包装器
            # 为了让原有代码中的全局变量不冲突，我们使用 exec 并在特定的 global 字典中运行
            exec_globals = {
                "st": st,
                "__file__": TacticalDashboardAdapter.SOURCE_PATH,
                "os": os,
                "__name__": "__main__"
            }
            
            # 可以在这里额外注入样式，确保仪表盘内容在暗色背景中显示（如果 RAG 是亮色的）
            # 或者让它自适应。这里我们先确保它不破坏全局。
            
            st.markdown("""
                <style>
                /* 局部暗色区域适配：仅在仪表盘标签页内使用 */
                .tactical-container { 
                    background-color: #0a0a0a; 
                    padding: 20px; 
                    border-radius: 12px;
                    color: #f8fafc;
                }
                </style>
            """, unsafe_allow_html=True)
            
            with st.container():
                exec(code, exec_globals)
                
        except Exception as e:
            st.error(f"🚨 战术仪表盘加载异常: {e}")
