#!/usr/bin/env python3
"""
从主页移除重复的性能监控面板
"""

def remove_duplicate_perf_monitor():
    with open('src/apppro.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 从主页移除性能监控面板（保留监控标签页中的）
    old_main_perf = '''        # v1.5.1: 性能监控面板
        perf_monitor.render_panel()

        st.markdown("---")'''
    
    new_main_content = '''        st.markdown("---")'''
    
    content = content.replace(old_main_perf, new_main_content)
    
    with open('src/apppro.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 已从主页移除重复的性能监控面板")
    print("🔍 现在性能监控只在监控标签页中存在")

if __name__ == "__main__":
    remove_duplicate_perf_monitor()
