import os
import json
import pandas as pd
import sqlite3
from typing import List, Dict, Any
import hashlib

class DataAnalystEngine:
    def __init__(self, kb_path: str, logger=None):
        self.kb_path = kb_path
        self.logger = logger
        self.db_path = os.path.join(kb_path, "business_data.db")
        self.schema_path = os.path.join(kb_path, "business_schema.json")
        self.blueprint_path = os.path.join(kb_path, "business_blueprint.json")

    def extract_schema_from_docs(self, docs: List[Any], model_client) -> Dict[str, Any]:
        """
        [核心升级] 语义化提取：从自然语言文档（PDF/Word）中识别表结构、数据字典。
        """
        # 合并所有文档的文本片段进行分析
        all_text = "\n".join([d.text for d in docs[:20]]) # 取前20个片段防止Token溢出
        
        prompt = f"""
你是一名顶级的数据库架构师。请从以下文档内容中提取出所有的数据库表结构、字段说明、数据字典及表间关联关系：
{all_text}

请输出一个标准的 JSON 对象，格式如下：
{{
  "tables": {{
    "表名": {{
      "description": "业务含义",
      "columns": [
        {{"name": "字段名", "type": "类型", "comment": "业务解释", "is_primary": true/false}}
      ],
      "foreign_keys": [
        {{"column": "本表字段", "ref_table": "关联表", "ref_column": "关联字段"}}
      ]
    }}
  }}
}}
请仅输出 JSON。
"""
        response = model_client.complete(prompt)
        try:
            schema_data = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
            with open(self.schema_path, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, indent=4, ensure_ascii=False)
            return schema_data
        except:
            return {"error": "语义解析失败"}

    def infer_business_blueprint(self, schemas: Dict[str, Any], model_client) -> Dict[str, Any]:
        """
        业务推演：推导出业务场景、关联路径和分析建议。
        """
        prompt = f"""
请根据以下数据库结构推导业务全景图：
{json.dumps(schemas, indent=2, ensure_ascii=False)}

请输出 JSON：
1. business_scenario: 业务系统描述。
2. core_logic: 核心业务流转逻辑。
3. analysis_dimensions: 推荐的 5 个业务分析维度。
"""
        response = model_client.complete(prompt)
        try:
            blueprint = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
            with open(self.blueprint_path, 'w', encoding='utf-8') as f:
                json.dump(blueprint, f, indent=4, ensure_ascii=False)
            return blueprint
        except:
            return {{}}

    def execute_analysis(self, query: str, model_client) -> Dict[str, Any]:
        """
        [主动分析版] 强制执行 SQL 并返回结构化结果
        """
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            schemas = json.load(f)
        
        # 1. 强制生成 SQL (哪怕问题模糊)
        sql_prompt = f"""
你是一名资深 SQL 专家。基于以下表结构，请生成一条 SQL 来回答用户的问题。
如果问题未指定具体个体（如“某个用户”），请默认查询“所有个体的汇总统计”或“前10名排行”。

表结构：{json.dumps(schemas, ensure_ascii=False)}

用户问题：{query}

要求：
1. 必须返回 SQL，不要反问用户。
2. SQL 必须包裹在 [SQL_START] 和 [SQL_END] 之间。
3. 如果需要计算总额，请使用 SUM()；如果需要计数，请使用 COUNT()。
"""
        sql_res = model_client.complete(sql_prompt).text
        sql_query = ""
        if "[SQL_START]" in sql_res:
            sql_query = sql_res.split("[SQL_START]")[1].split("[SQL_END]")[0].strip()
        
        # 2. 尝试执行
        execution_result = {"success": False}
        if sql_query:
            execution_result = self.execute_sql(sql_query)
        
        # 3. 最终业务解读
        summary_prompt = f"""
根据以下 SQL 执行结果，请为用户提供一份简洁的业务分析报告：
SQL: {sql_query}
结果数据: {json.dumps(execution_result.get('data', [])[:10], ensure_ascii=False)}
问题: {query}

报告结构：
- [💡 逻辑推演]：说明查询了哪些表及字段。
- [📊 核心发现]：用一句话总结数据发现。
- [📈 仿真建议]：说明后续可以关注的业务指标。
"""
        final_report = model_client.complete(summary_prompt).text
        
        return {
            "sql": sql_query,
            "data": execution_result.get('data', []),
            "logic": final_report,
            "success": execution_result.get('success', False)
        }

    def process_files(self, file_paths: List[str]):
        # 保留原有的 CSV/Excel 处理能力供 fallback
        pass