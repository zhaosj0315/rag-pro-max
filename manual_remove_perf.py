#!/usr/bin/env python3
"""
手动精确移除主页性能监控
"""

def manual_remove_perf():
    with open('src/apppro.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 找到并移除主页中的性能监控面板（第490行附近）
    new_lines = []
    skip_lines = False
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # 在主页部分找到性能监控面板并跳过
        if line_num == 489 and "# v1.5.1: 性能监控面板" in line:
            skip_lines = True
            continue
        elif line_num == 490 and "perf_monitor.render_panel()" in line:
            continue
        elif line_num == 491 and line.strip() == "":
            continue
        elif skip_lines and "st.markdown(\"---\")" in line:
            skip_lines = False
            new_lines.append(line)
            continue
        
        if not skip_lines:
            new_lines.append(line)
    
    with open('src/apppro.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ 手动移除主页性能监控完成")

if __name__ == "__main__":
    manual_remove_perf()
