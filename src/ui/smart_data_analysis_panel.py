"""智能数据分析面板 - 使用关联分析和智能 SQL 生成"""
import streamlit as st
from typing import Dict, Any
from src.analysis import DBSchemaParser
from src.analysis.smart_sql_generator import SmartSQLGenerator
from src.analysis.relation_analyzer import RelationAnalyzer


def render_smart_data_analysis_panel(kb_name: str, kb_documents: Dict[str, Any]):
    """渲染智能数据分析面板"""
    
    st.subheader("📊 智能数据分析")
    
    # 步骤1: 上传数据字典
    st.write("**步骤1: 上传数据字典或表结构定义**")
    uploaded_file = st.file_uploader(
        "上传数据字典 (支持 .txt, .md, .sql, .json)",
        type=["txt", "md", "sql", "json"],
        key=f"smart_db_schema_{kb_name}"
    )
    
    schema_info = None
    if uploaded_file:
        content = uploaded_file.read().decode("utf-8")
        parser = DBSchemaParser()
        schema_info = parser.parse_from_text(content)
        
        st.success(f"✅ 解析成功: 发现 {schema_info['table_count']} 个表")
        
        # 显示表结构和关联关系
        with st.expander("📋 表结构和关联分析"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**表结构:**")
                for table_name, table_info in schema_info["tables"].items():
                    st.write(f"- **{table_name}**")
                    st.write(f"  主键: {table_info['primary_key']}")
                    st.write(f"  字段: {', '.join(table_info['field_names'])}")
            
            with col2:
                st.write("**表间关联:**")
                analyzer = RelationAnalyzer(schema_info)
                st.write(analyzer.get_relation_summary())
    
    # 步骤2: 输入数据分析需求
    st.write("**步骤2: 输入数据分析需求**")
    requirement = st.text_area(
        "描述你的数据分析需求",
        placeholder="例如: 查询每个用户的订单总数和平均金额",
        key=f"smart_requirement_{kb_name}"
    )
    
    # 步骤3: 智能生成 SQL
    if schema_info and requirement:
        if st.button("🤖 智能生成SQL查询", key=f"smart_gen_sql_{kb_name}"):
            generator = SmartSQLGenerator(schema_info)
            result = generator.generate_smart_query(requirement)
            
            # 显示分析结果
            st.write("**📊 查询分析:**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**推荐方案:** {result['explanation']}")
            with col2:
                if result['plan']:
                    st.write(f"**推荐度:** {result['plan']['score']}/100")
            
            # 显示关联关系
            if result['plan'] and result['plan']['joins']:
                st.write("**关联关系:**")
                for join in result['plan']['joins']:
                    st.write(f"- {join['left_table']}.{join['left_field']} = {join['right_table']}.{join['right_field']}")
            
            # 显示生成的 SQL
            st.write("**生成的SQL查询:**")
            st.code(result['sql'], language="sql")
            
            # 显示详细分析
            with st.expander("📈 详细分析"):
                analyzer = RelationAnalyzer(schema_info)
                analysis = result['analysis']
                
                if analysis['mentioned_tables']:
                    st.write(f"**提到的表:** {', '.join(analysis['mentioned_tables'])}")
                
                if analysis['mentioned_fields']:
                    st.write(f"**提到的字段:** {', '.join(analysis['mentioned_fields'])}")
                
                st.write("**所有推荐方案:**")
                for i, rec in enumerate(analysis['recommendations'], 1):
                    st.write(f"{i}. {rec['reason']} (推荐度: {rec['score']}/100)")
    
    elif requirement and not schema_info:
        st.warning("⚠️ 请先上传数据字典或表结构定义")
    
    # 步骤4: 表关联可视化
    if schema_info:
        st.write("**步骤3: 表关联关系可视化**")
        
        analyzer = RelationAnalyzer(schema_info)
        
        # 选择表查看其连接
        selected_table = st.selectbox(
            "选择表查看其连接关系",
            list(schema_info["tables"].keys()),
            key=f"table_select_{kb_name}"
        )
        
        if selected_table:
            connections = analyzer.get_table_connections(selected_table)
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**{selected_table} 的出站连接:**")
                if connections['outgoing']:
                    for target in connections['outgoing']:
                        st.write(f"- → {target}")
                else:
                    st.write("(无出站连接)")
            
            with col2:
                st.write(f"**{selected_table} 的入站连接:**")
                if connections['incoming']:
                    for source in connections['incoming']:
                        st.write(f"- ← {source}")
                else:
                    st.write("(无入站连接)")
