import sys
import os

file_path = "src/apppro.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

# Find start: select_col1, select_col2, select_col3 = st.columns([0.6, 5.9, 0.5])
for i, line in enumerate(lines):
    if i < 1200: continue
    if 'select_col1, select_col2, select_col3 = st.columns([0.6, 5.9, 0.5])' in line:
        start_idx = i
        break

# Find end: before "# 知识库搜索/过滤已按用户要求移除"
for i, line in enumerate(lines):
    if i < 1300: continue
    if '# 知识库搜索/过滤已按用户要求移除' in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    print(f"Refining fragment at {start_idx} to {end_idx}")
    
    # We need to initialize selected_nav before the fragment so it's available globally.
    # But wait, we should also ensure current_nav is synced.
    
    # First, let's look at the original block again to see what variables we need.
    # selected_nav, is_pure_chat, target_kb_id, selected_kbs.
    
    init_vars = [
        "        # 初始化选择变量，防止 NameError\n",
        "        if 'selected_nav' not in st.session_state: st.session_state.selected_nav = nav_options[default_idx]\n",
        "        selected_nav = st.session_state.selected_nav\n"
    ]
    
    wrapper_start = [
        "        # [UI Optimization] 知识库选择与自动启动独立渲染 (无感加载)\n",
        "        @st.fragment\n",
        "        def render_kb_selector_and_autostart():\n"
    ]
    
    # We need to capture variables from outer scope if they are needed inside.
    # nav_options, default_idx, output_base, embed_provider, etc.
    # Python closures handle this.
    
    block = lines[start_idx:end_idx]
    
    # Process the block to:
    # 1. Use st.session_state.selected_nav instead of local.
    # 2. Add scope="app" to reruns that should trigger main area update.
    
    new_block = []
    for line in block:
        if 'selected_nav = st.selectbox' in line:
            # Update session state on selectbox change
            new_block.append(line.replace('selected_nav =', 'st.session_state.selected_nav ='))
            new_block.append("            selected_nav = st.session_state.selected_nav\n")
        elif 'selected_nav' in line and '=' not in line:
            # Access from session state? No, local 'selected_nav' will be set right after selectbox.
            new_block.append(line)
        elif "st.rerun()" in line:
            # Success cases need scope="app"
            if "pure_chat" in line or "启动" in line or "target_kb_id" in line:
                 new_block.append(line.replace("st.rerun()", "st.rerun(scope='app')"))
            else:
                 new_block.append(line)
        else:
            new_block.append(line)

    indented_block = ["    " + line for line in new_block]
    
    wrapper_end = [
        "\n",
        "        render_kb_selector_and_autostart()\n",
        "        selected_nav = st.session_state.selected_nav\n" # Export to global scope
    ]
    
    new_lines = lines[:start_idx] + init_vars + wrapper_start + indented_block + wrapper_end + lines[end_idx:]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("Success!")
else:
    print("Markers not found.")