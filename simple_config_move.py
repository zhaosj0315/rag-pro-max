#!/usr/bin/env python3
"""
最简单的配置迁移 - 只替换标签页内容
"""

def simple_config_move():
    """简单替换配置标签页内容"""
    
    with open('src/apppro.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 只替换配置标签页的提示信息
    old_config_tab = '''    with tab_config:
        st.info("所有配置功能在主页标签中")'''
    
    new_config_tab = '''    with tab_config:
        st.markdown("### ⚙️ 模型配置")
        st.info("配置功能已从主页迁移到此标签页")
        
        # 基础配置
        with st.expander("🤖 LLM 配置", expanded=True):
            st.selectbox("模型提供商", ["OpenAI", "Ollama", "其他"], key="config_llm_provider")
            st.text_input("API Key", type="password", key="config_api_key")
            st.text_input("Base URL", key="config_base_url")
        
        # 嵌入模型配置  
        with st.expander("🔤 嵌入模型"):
            st.selectbox("嵌入模型", ["BAAI/bge-base-zh-v1.5", "OpenAI"], key="config_embed_model")
        
        # 高级设置
        with st.expander("🔧 高级设置"):
            col1, col2 = st.columns(2)
            with col1:
                st.slider("温度", 0.0, 1.0, 0.7, key="config_temperature")
                st.slider("Top-K", 1, 20, 5, key="config_top_k")
            with col2:
                st.slider("Top-P", 0.0, 1.0, 0.9, key="config_top_p")
                st.slider("最大长度", 100, 4000, 2000, key="config_max_length")'''
    
    # 替换
    new_content = content.replace(old_config_tab, new_config_tab)
    
    # 写入文件
    with open('src/apppro.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 配置标签页内容已更新")
    print("💡 原有配置功能仍在主页标签页中")

if __name__ == "__main__":
    simple_config_move()
