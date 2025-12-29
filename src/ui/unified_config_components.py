#!/usr/bin/env python3
"""
统一配置组件
整合所有配置相关的UI渲染函数，消除重复代码
"""

import streamlit as st
from typing import Dict, Any, Optional, List, Tuple
import json
import os

class UnifiedConfigRenderer:
    """统一配置渲染器"""
    
    def __init__(self):
        self.config_cache = {}
    
    def render_basic_config(self, config_data: Dict[str, Any], key_prefix: str = "basic") -> Dict[str, Any]:
        """渲染基础配置表单"""
        updated_config = {}
        
        with st.expander("🔧 基础配置", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                # 模型配置
                st.markdown("##### 🤖 模型设置")
                updated_config['default_model'] = st.selectbox(
                    "默认模型",
                    options=['gpt-3.5-turbo', 'gpt-4', 'qwen2.5:7b', 'llama3.1:8b'],
                    index=0 if 'default_model' not in config_data else 
                          ['gpt-3.5-turbo', 'gpt-4', 'qwen2.5:7b', 'llama3.1:8b'].index(config_data.get('default_model', 'gpt-3.5-turbo')),
                    key=f"{key_prefix}_model"
                )
                
                updated_config['temperature'] = st.slider(
                    "温度",
                    min_value=0.0,
                    max_value=2.0,
                    value=config_data.get('temperature', 0.7),
                    step=0.1,
                    key=f"{key_prefix}_temp"
                )
            
            with col2:
                # 检索配置
                st.markdown("##### 🔍 检索设置")
                updated_config['top_k'] = st.number_input(
                    "检索数量",
                    min_value=1,
                    max_value=20,
                    value=config_data.get('top_k', 5),
                    key=f"{key_prefix}_topk"
                )
                
                updated_config['similarity_threshold'] = st.slider(
                    "相似度阈值",
                    min_value=0.0,
                    max_value=1.0,
                    value=config_data.get('similarity_threshold', 0.7),
                    step=0.05,
                    key=f"{key_prefix}_sim"
                )
        
        return updated_config
    
    def render_embedding_config(self, config_data: Dict[str, Any], key_prefix: str = "embed") -> Dict[str, Any]:
        """渲染嵌入模型配置表单"""
        updated_config = {}
        
        with st.expander("🧠 嵌入模型配置", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### 📊 模型选择")
                updated_config['embedding_model'] = st.selectbox(
                    "嵌入模型",
                    options=[
                        'sentence-transformers/all-MiniLM-L6-v2',
                        'sentence-transformers/all-mpnet-base-v2',
                        'text-embedding-ada-002',
                        'bge-large-zh-v1.5'
                    ],
                    index=0 if 'embedding_model' not in config_data else 0,
                    key=f"{key_prefix}_model"
                )
                
                updated_config['chunk_size'] = st.number_input(
                    "文档分块大小",
                    min_value=100,
                    max_value=2000,
                    value=config_data.get('chunk_size', 512),
                    step=50,
                    key=f"{key_prefix}_chunk"
                )
            
            with col2:
                st.markdown("##### ⚡ 性能设置")
                updated_config['batch_size'] = st.number_input(
                    "批处理大小",
                    min_value=1,
                    max_value=100,
                    value=config_data.get('batch_size', 32),
                    key=f"{key_prefix}_batch"
                )
                
                updated_config['use_gpu'] = st.checkbox(
                    "启用GPU加速",
                    value=config_data.get('use_gpu', True),
                    key=f"{key_prefix}_gpu"
                )
        
        return updated_config
    
    def render_advanced_config(self, config_data: Dict[str, Any], key_prefix: str = "advanced") -> Dict[str, Any]:
        """渲染高级配置表单"""
        updated_config = {}
        
        with st.expander("⚙️ 高级配置", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### 🔄 缓存设置")
                updated_config['enable_cache'] = st.checkbox(
                    "启用缓存",
                    value=config_data.get('enable_cache', True),
                    key=f"{key_prefix}_cache"
                )
                
                updated_config['cache_ttl'] = st.number_input(
                    "缓存过期时间(秒)",
                    min_value=60,
                    max_value=86400,
                    value=config_data.get('cache_ttl', 3600),
                    key=f"{key_prefix}_ttl"
                )
            
            with col2:
                st.markdown("##### 📝 日志设置")
                updated_config['log_level'] = st.selectbox(
                    "日志级别",
                    options=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                    index=['DEBUG', 'INFO', 'WARNING', 'ERROR'].index(config_data.get('log_level', 'INFO')),
                    key=f"{key_prefix}_log"
                )
                
                updated_config['max_log_files'] = st.number_input(
                    "最大日志文件数",
                    min_value=1,
                    max_value=100,
                    value=config_data.get('max_log_files', 10),
                    key=f"{key_prefix}_maxlog"
                )
        
        return updated_config
    
    def render_config_tab(self, tab_name: str, config_data: Dict[str, Any], 
                         sections: List[str] = None) -> Dict[str, Any]:
        """渲染完整的配置标签页"""
        if sections is None:
            sections = ['basic', 'embedding', 'advanced']
        
        st.markdown(f"#### ⚙️ {tab_name}")
        
        all_config = {}
        
        # 渲染各个配置部分
        if 'basic' in sections:
            basic_config = self.render_basic_config(config_data, f"{tab_name.lower()}_basic")
            all_config.update(basic_config)
        
        if 'embedding' in sections:
            embed_config = self.render_embedding_config(config_data, f"{tab_name.lower()}_embed")
            all_config.update(embed_config)
        
        if 'advanced' in sections:
            advanced_config = self.render_advanced_config(config_data, f"{tab_name.lower()}_advanced")
            all_config.update(advanced_config)
        
        # 配置操作按钮
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 保存配置", key=f"{tab_name.lower()}_save"):
                self._save_config(all_config, tab_name.lower())
                st.success("配置已保存！")
        
        with col2:
            if st.button("🔄 重置配置", key=f"{tab_name.lower()}_reset"):
                st.session_state.clear()
                st.rerun()
        
        with col3:
            if st.button("📥 导入配置", key=f"{tab_name.lower()}_import"):
                uploaded_file = st.file_uploader("选择配置文件", type=['json'])
                if uploaded_file:
                    imported_config = json.load(uploaded_file)
                    all_config.update(imported_config)
                    st.success("配置已导入！")
        
        return all_config
    
    def _save_config(self, config_data: Dict[str, Any], config_name: str):
        """保存配置到文件"""
        config_dir = "config"
        os.makedirs(config_dir, exist_ok=True)
        
        config_file = os.path.join(config_dir, f"{config_name}_config.json")
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            st.error(f"保存配置失败: {e}")
    
    def load_config(self, config_name: str) -> Dict[str, Any]:
        """从文件加载配置"""
        config_file = os.path.join("config", f"{config_name}_config.json")
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # 返回默认配置
        return {
            'default_model': 'gpt-3.5-turbo',
            'temperature': 0.7,
            'top_k': 5,
            'similarity_threshold': 0.7,
            'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2',
            'chunk_size': 512,
            'batch_size': 32,
            'use_gpu': True,
            'enable_cache': True,
            'cache_ttl': 3600,
            'log_level': 'INFO',
            'max_log_files': 10
        }

# 全局实例
unified_config_renderer = UnifiedConfigRenderer()

# 便捷函数
def render_basic_config(config_data: Dict[str, Any], key_prefix: str = "basic") -> Dict[str, Any]:
    """渲染基础配置 - 便捷函数"""
    return unified_config_renderer.render_basic_config(config_data, key_prefix)

def render_embedding_config(config_data: Dict[str, Any], key_prefix: str = "embed") -> Dict[str, Any]:
    """渲染嵌入配置 - 便捷函数"""
    return unified_config_renderer.render_embedding_config(config_data, key_prefix)

def render_config_tab(tab_name: str, config_data: Dict[str, Any], 
                     sections: List[str] = None) -> Dict[str, Any]:
    """渲染配置标签页 - 便捷函数"""
    return unified_config_renderer.render_config_tab(tab_name, config_data, sections)
