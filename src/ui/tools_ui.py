"""
工具箱界面 - 负责 "🔧 工具" 标签页的渲染和交互
"""

import streamlit as st
import time
import psutil
import subprocess
import platform

class ToolsUI:
    """工具箱 UI"""
    
    @staticmethod
    def render():
        """渲染工具箱界面"""
        st.markdown("#### 🔧 工具箱")
        
        # 知识库管理入口
        with st.expander("📚 知识库管理", expanded=True):
            st.info("💡 请前往 **主页 -> 知识库控制台** 进行知识库管理")
            if st.button("🚀 跳转到知识库管理", use_container_width=True):
                # 实际上 Streamlit 不支持直接跳转 Tab，我们通过 Session State 提示用户
                st.toast("请点击左侧侧边栏顶部的 '🏠 主页' 标签")
        
        # 系统工具（默认展开）
        with st.expander("🛠️ 系统工具", expanded=True):
            # 系统监控
            auto_refresh = st.checkbox("🔄 自动刷新 (2秒)", value=False, key="tools_auto_refresh")

            monitor_placeholder = st.empty()

            cpu_percent = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            gpu_active = False
            if platform.system() == 'Darwin':
                try:
                    result = subprocess.run(['ioreg', '-r', '-d', '1', '-w', '0', '-c', 'IOAccelerator'],
                                          capture_output=True, text=True, timeout=1)
                    if 'PerformanceStatistics' in result.stdout:
                        gpu_active = True
                except:
                    pass

            with monitor_placeholder.container():
                # 优化为 2*3 布局 (一行两个)
                m_row1_col1, m_row1_col2 = st.columns(2)
                m_row2_col1, m_row2_col2 = st.columns(2)
                m_row3_col1, m_row3_col2 = st.columns(2)

                with m_row1_col1:
                    st.metric("CPU 使用率", f"{cpu_percent:.1f}%")
                    st.caption(f"⚙️ {psutil.cpu_count()} 核")
                    st.progress(cpu_percent / 100)

                with m_row1_col2:
                    st.metric("GPU 状态", "活跃" if gpu_active else "空闲")
                    st.caption("🎮 Apple Metal")
                    if gpu_active:
                        st.progress(0.5)
                    else:
                        st.progress(0.0)

                with m_row2_col1:
                    st.metric("内存使用", f"{mem.percent:.1f}%")
                    st.caption(f"🧠 {mem.used/1024**3:.1f}GB / {mem.total/1024**3:.1f}GB")
                    st.progress(mem.percent / 100)

                with m_row2_col2:
                    st.metric("磁盘使用", f"{disk.percent:.1f}%")
                    st.caption(f"💾 {disk.used/1024**3:.0f}GB / {disk.total/1024**3:.0f}GB")
                    st.progress(disk.percent / 100)

                current_proc = psutil.Process()
                proc_mem = current_proc.memory_info().rss / 1024**3
                
                with m_row3_col1:
                    st.metric("进程内存", f"{proc_mem:.1f} GB")
                    st.caption("🔍 当前应用占用")
                
                with m_row3_col2:
                    st.metric("线程数量", f"{current_proc.num_threads()}")
                    st.caption("🧵 活动线程数")

                st.caption("💡 GPU 详细信息需要: `sudo python3 system_monitor.py`")

            if auto_refresh:
                time.sleep(2)
                st.rerun()
        
        st.markdown("---")
        st.markdown("##### ⬆️ 快速上传")
        uploaded_file = st.file_uploader("选择文件", type=['pdf', 'txt', 'docx', 'md'], key="tools_uploader")
        if uploaded_file:
            st.success(f"✅ 已选择: {uploaded_file.name}")
            st.info("💡 请到主页完成处理")
