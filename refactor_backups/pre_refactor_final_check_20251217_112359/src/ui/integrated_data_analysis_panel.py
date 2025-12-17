"""完整集成的数据分析面板 - 从知识库上传到 SQL 生成"""
import streamlit as st
from typing import Dict, Any
from src.analysis import DBSchemaParser
from src.analysis.smart_sql_generator import SmartSQLGenerator
from src.analysis.relation_analyzer import RelationAnalyzer
from src.analysis.recommendation_engine import RecommendationEngine


def render_integrated_data_analysis(kb_name: str, kb_documents: Dict[str, Any]):
    """渲染完整集成的数据分析面板"""
    
    st.subheader("📊 智能数据分析")
    
    # 初始化 session state
    if f"schema_info_{kb_name}" not in st.session_state:
        st.session_state[f"schema_info_{kb_name}"] = None
    
    # 步骤1: 检查是否有上传的数据字典
    st.write("**步骤1: 数据字典**")
    
    # 从知识库文档中查找数据字典
    schema_info = None
    dict_files = []
    
    if kb_documents:
        for doc_name, doc_content in kb_documents.items():
            if any(ext in doc_name.lower() for ext in ['.sql', '.md', '.txt', '.json']):
                dict_files.append(doc_name)
    
    if dict_files:
        st.success(f"✅ 发现 {len(dict_files)} 个数据字典文件")
        
        # 选择要分析的文件
        selected_file = st.selectbox(
            "选择数据字典文件",
            dict_files,
            key=f"dict_file_{kb_name}"
        )
        
        if selected_file and kb_documents.get(selected_file):
            # 解析数据字典
            parser = DBSchemaParser()
            schema_info = parser.parse_from_text(kb_documents[selected_file])
            st.session_state[f"schema_info_{kb_name}"] = schema_info
            
            st.success(f"✅ 解析成功: 发现 {schema_info['table_count']} 个表")
    else:
        st.info("💡 请先在左侧知识库管理中上传数据字典文件 (.sql, .md, .txt, .json)")
        return
    
    # 如果没有解析成功，尝试从 session state 获取
    if not schema_info:
        schema_info = st.session_state.get(f"schema_info_{kb_name}")
    
    if not schema_info:
        return
    
    # 步骤2: 显示数据库摘要和推荐问题
    st.write("**步骤2: 数据库分析**")
    
    recommender = RecommendationEngine(schema_info)
    
    # 显示摘要
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(recommender.generate_summary())
    
    with col2:
        st.write("**表间关联:**")
        for rel_desc in recommender.get_relation_descriptions():
            st.write(rel_desc)
    
    # 步骤3: 显示常见问题
    st.write("**步骤3: 常见问题**")
    
    common_questions = recommender.generate_common_questions()
    
    if common_questions:
        st.write("点击下面的问题，系统将自动生成相应的 SQL 查询:")
        
        # 创建问题按钮
        for i, q in enumerate(common_questions):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**{q['question']}**")
            
            with col2:
                if st.button("查询", key=f"btn_{kb_name}_{i}"):
                    # 生成 SQL
                    generator = SmartSQLGenerator(schema_info)
                    result = generator.generate_smart_query(q['query'])
                    
                    # 显示结果
                    st.write("**生成的 SQL:**")
                    st.code(result['sql'], language="sql")
                    
                    st.write(f"**推荐理由:** {result['explanation']}")
                    
                    if result['plan']:
                        st.write(f"**推荐度:** {result['plan']['score']}/100")
    
    # 步骤4: 自定义查询
    st.write("**步骤4: 自定义查询**")
    
    custom_query = st.text_area(
        "输入你的数据分析需求",
        placeholder="例如: 查询销售额最高的产品",
        key=f"custom_query_{kb_name}"
    )
    
    if custom_query:
        if st.button("🚀 生成 SQL", key=f"custom_btn_{kb_name}"):
            generator = SmartSQLGenerator(schema_info)
            result = generator.generate_smart_query(custom_query)
            
            st.write("**生成的 SQL:**")
            st.code(result['sql'], language="sql")
            
            st.write(f"**推荐理由:** {result['explanation']}")
            
            if result['plan']:
                st.write(f"**推荐度:** {result['plan']['score']}/100")
                
                if result['plan']['joins']:
                    st.write("**关联关系:**")
                    for join in result['plan']['joins']:
                        st.write(f"- {join['left_table']}.{join['left_field']} = {join['right_table']}.{join['right_field']}")
    
    # 步骤5: 表结构详情
    st.write("**步骤5: 表结构详情**")
    
    with st.expander("📋 查看所有表的详细信息"):
        table_descriptions = recommender.get_table_descriptions()
        
        for table_name, description in table_descriptions.items():
            st.write(description)
