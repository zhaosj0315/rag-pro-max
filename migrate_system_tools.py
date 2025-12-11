#!/usr/bin/env python3
"""
迁移系统工具到工具标签页
"""

def migrate_system_tools():
    with open('src/apppro.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份
    with open('src/apppro.py.backup_system_tools', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 找到系统工具代码段
    tools_start = content.find('        # P0改进3: 系统工具（默认折叠）')
    tools_end = content.find('        st.markdown("---")\n        st.markdown("### 💠 知识库控制台")')
    
    if tools_start == -1 or tools_end == -1:
        print("❌ 未找到系统工具代码段")
        return False
    
    # 提取系统工具代码
    system_tools_code = content[tools_start:tools_end].strip()
    
    # 从主页移除系统工具
    content_without_tools = content[:tools_start] + content[tools_end:]
    
    # 更新工具标签页，替换现有的简单内容
    old_tools_tab = '''    with tab_tools:
        st.markdown("### 🔧 工具箱")
        st.markdown("#### 📚 知识库管理")
        
        # 简化的知识库选择
        default_output_path = os.path.join(os.getcwd(), "vector_db_storage")
        if os.path.exists(default_output_path):
            existing_kbs = [d for d in os.listdir(default_output_path) 
                          if os.path.isdir(os.path.join(default_output_path, d))]
            if existing_kbs:
                selected_kb = st.selectbox("选择知识库", existing_kbs)
                st.info(f"📂 当前知识库: {selected_kb}")
            else:
                st.info("📝 暂无知识库，请在主页创建")
        else:
            st.info("📝 暂无知识库，请在主页创建")
        
        st.markdown("#### ⬆️ 快速上传")
        uploaded_file = st.file_uploader("选择文件", type=['pdf', 'txt', 'docx', 'md'])
        if uploaded_file:
            st.success(f"✅ 已选择: {uploaded_file.name}")
            st.info("💡 请到主页完成处理")'''
    
    # 重新缩进系统工具代码（增加4个空格）
    tools_lines = system_tools_code.split('\n')
    indented_tools_lines = []
    
    for line in tools_lines:
        if line.strip():  # 非空行
            indented_tools_lines.append('    ' + line)
        else:  # 空行
            indented_tools_lines.append('')
    
    indented_tools_code = '\n'.join(indented_tools_lines)
    
    new_tools_tab = f'''    with tab_tools:
        st.markdown("### 🔧 工具箱")
        
{indented_tools_code}
        
        st.markdown("---")
        st.markdown("#### ⬆️ 快速上传")
        uploaded_file = st.file_uploader("选择文件", type=['pdf', 'txt', 'docx', 'md'], key="tools_uploader")
        if uploaded_file:
            st.success(f"✅ 已选择: {uploaded_file.name}")
            st.info("💡 请到主页完成处理")'''
    
    # 替换工具标签页内容
    final_content = content_without_tools.replace(old_tools_tab, new_tools_tab)
    
    # 写入文件
    with open('src/apppro.py', 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print("✅ 系统工具已迁移到工具标签页")
    print("🔍 迁移内容：")
    print("   - 🛠️ 系统工具 (CPU/GPU/内存/磁盘监控)")
    print("   - 🔄 自动刷新功能")
    print("   - 📊 实时性能指标")
    print("   - ⬆️ 快速文件上传")
    return True

if __name__ == "__main__":
    migrate_system_tools()
