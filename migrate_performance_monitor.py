#!/usr/bin/env python3
"""
迁移性能监控到监控标签页
"""

def migrate_performance_monitor():
    with open('src/apppro.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份
    with open('src/apppro.py.backup_perf_monitor', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 从主页移除性能监控面板
    old_perf_panel = '''        # v1.5.1: 性能监控面板
        perf_monitor.render_panel()

        st.markdown("---")'''
    
    content = content.replace(old_perf_panel, '        st.markdown("---")')
    
    # 替换监控标签页内容
    old_monitor_tab = '''    with tab_monitor:
        st.info("所有监控功能在主页标签中")'''
    
    new_monitor_tab = '''    with tab_monitor:
        st.markdown("### 📊 系统监控")
        
        # v1.5.1: 性能监控面板
        perf_monitor.render_panel()'''
    
    content = content.replace(old_monitor_tab, new_monitor_tab)
    
    # 写入文件
    with open('src/apppro.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 性能监控已迁移到监控标签页")
    print("🔍 迁移内容：")
    print("   - 📊 查询性能 (平均耗时、最快、最慢)")
    print("   - 📈 查询统计 (总查询数、总耗时)")
    print("   - 🔄 刷新/清空按钮")

if __name__ == "__main__":
    migrate_performance_monitor()
