#!/usr/bin/env python3
"""
手动修复工具标签页内容
"""

def manual_fix_tools_tab():
    with open('src/apppro.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份
    with open('src/apppro.py.backup_manual_tools', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 替换工具标签页的简单内容
    old_tools_content = '''    with tab_tools:
        st.info("所有工具功能在主页标签中")'''
    
    new_tools_content = '''    with tab_tools:
        st.markdown("### 🔧 工具箱")
        
        # P0改进3: 系统工具（默认展开）
        with st.expander("🛠️ 系统工具", expanded=True):
            # 系统监控
            auto_refresh = st.checkbox("🔄 自动刷新 (2秒)", value=False, key="tools_auto_refresh")

            monitor_placeholder = st.empty()

            import psutil
            import subprocess
            cpu_percent = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/System/Volumes/Data')

            gpu_active = False
            try:
                result = subprocess.run(['ioreg', '-r', '-d', '1', '-w', '0', '-c', 'IOAccelerator'],
                                      capture_output=True, text=True, timeout=1)
                if 'PerformanceStatistics' in result.stdout:
                    gpu_active = True
            except:
                pass

            with monitor_placeholder.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.metric("CPU 使用率", f"{cpu_percent:.1f}%")
                with col2:
                    st.caption(f"{psutil.cpu_count()} 核")
                st.progress(cpu_percent / 100)

                col1, col2 = st.columns([3, 1])
                with col1:
                    st.metric("GPU 状态", "活跃" if gpu_active else "空闲")
                with col2:
                    st.caption("32 核")
                if gpu_active:
                    st.progress(0.5)
                else:
                    st.progress(0.0)

                col1, col2 = st.columns([3, 1])
                with col1:
                    st.metric("内存使用", f"{mem.percent:.1f}%")
                with col2:
                    st.caption(f"{mem.used/1024**3:.1f}GB")
                st.progress(mem.percent / 100)

                col1, col2 = st.columns([3, 1])
                with col1:
                    st.metric("磁盘使用", f"{disk.percent:.1f}%")
                with col2:
                    st.caption(f"{disk.used/1024**3:.0f}GB")
                st.progress(disk.percent / 100)

                current_proc = psutil.Process()
                proc_mem = current_proc.memory_info().rss / 1024**3
                st.caption(f"🔍 进程: {proc_mem:.1f}GB | {current_proc.num_threads()} 线程")
                st.caption("💡 GPU 详细信息需要: `sudo python3 system_monitor.py`")

            if auto_refresh:
                import time
                time.sleep(2)
                st.rerun()
        
        st.markdown("---")
        st.markdown("#### ⬆️ 快速上传")
        uploaded_file = st.file_uploader("选择文件", type=['pdf', 'txt', 'docx', 'md'], key="tools_uploader")
        if uploaded_file:
            st.success(f"✅ 已选择: {uploaded_file.name}")
            st.info("💡 请到主页完成处理")'''
    
    # 替换内容
    content = content.replace(old_tools_content, new_tools_content)
    
    # 写入文件
    with open('src/apppro.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 工具标签页内容已手动修复")
    print("🔍 现在包含完整的系统工具功能")

if __name__ == "__main__":
    manual_fix_tools_tab()
