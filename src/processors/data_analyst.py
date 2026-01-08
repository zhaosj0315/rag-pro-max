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

    def infer_business_blueprint(self, schemas: Dict[str, Any], model_client) -> Dict[str, Any]:
        """
        [核心] 业务推演：分析表结构、字段名，推导出业务场景、关联路径和分析建议。
        """
        prompt = f"""
你是一名资深的业务架构师。请深入分析以下数据库表结构，并推导出其背后的业务逻辑：
{json.dumps(schemas, indent=2, ensure_ascii=False)}

请输出一个 JSON 格式的“业务蓝图”，包含：
1. business_scenario: 简要描述这是什么业务系统。
2. core_entities: 核心业务实体及其作用。
3. relationships: 表与表之间的关联路径（包含关联字段）。
4. analytical_suggestions: 基于此结构，可以进行的 3-5 个深度分析维度（如：用户生命周期、订单转化率）。

请仅输出 JSON 内容。
"""
        response = model_client.complete(prompt)
        try:
            blueprint = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
            with open(self.blueprint_path, 'w', encoding='utf-8') as f:
                json.dump(blueprint, f, indent=4, ensure_ascii=False)
            return blueprint
        except:
            return {"error": "推演失败"}

    def simulate_mock_data(self, schemas: Dict[str, Any], blueprint: Dict[str, Any], model_client):
        """
        [核心] 仿真模拟：如果表是空的，根据业务蓝图生成高质量模拟数据并注入。
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for table_name, info in schemas.items():
            # 检查表是否为空
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            if cursor.fetchone()[0] == 0:
                if self.logger: self.logger.info(f"🧪 正在为 {table_name} 生成仿真模拟数据...")
                
                sim_prompt = f"""
请为表 {table_name} 生成 10 条符合业务逻辑的模拟数据。
表结构: {json.dumps(info, ensure_ascii=False)}
业务背景: {blueprint.get('business_scenario', '通用业务')}
要求：
1. 必须符合字段类型。
2. 关联字段（如 ID）必须与该业务蓝图中的其他实体保持一致。
3. 仅返回 JSON 数组格式的数据。
"""
                response = model_client.complete(sim_prompt)
                try:
                    mock_data = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
                    df_mock = pd.DataFrame(mock_data)
                    df_mock.to_sql(table_name, conn, if_exists='append', index=False)
                except:
                    continue
        
        conn.close()

    def _sanitize_table_name(self, name: str) -> str:
        # 去除扩展名并保留合法字符
        base = os.path.splitext(name)[0]
        clean = "".join([c if c.isalnum() else "_" for c in base])
        return f"tbl_{clean.lower()}"

    def _extract_df_info(self, df: pd.DataFrame, source_desc: str) -> Dict[str, Any]:
        return {
            "source": source_desc,
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "row_count": len(df),
            "sample_data": df.head(3).to_dict(orient='records')
        }

    def process_files(self, file_paths: List[str]):
        """
        全量处理文件：
        1. 识别并提取表格内容
        2. 自动建立 SQL 表
        3. 调用 LLM 生成语义 Schema 和关联关系
        """
        all_schemas = {}
        conn = sqlite3.connect(self.db_path)
        
        for fp in file_paths:
            ext = os.path.splitext(fp)[1].lower()
            try:
                if ext == '.csv':
                    df = pd.read_csv(fp)
                    table_name = self._sanitize_table_name(os.path.basename(fp))
                    df.to_sql(table_name, conn, if_exists='replace', index=False)
                    all_schemas[table_name] = self._extract_df_info(df, "CSV数据表")
                
                elif ext in ['.xlsx', '.xls']:
                    excel_data = pd.read_excel(fp, sheet_name=None)
                    for sheet_name, df in excel_data.items():
                        table_name = self._sanitize_table_name(f"{os.path.basename(fp)}_{sheet_name}")
                        df.to_sql(table_name, conn, if_exists='replace', index=False)
                        all_schemas[table_name] = self._extract_df_info(df, f"Excel工作表: {sheet_name}")
                
                # TODO: 以后扩展 PDF/Word 中的表格提取逻辑
            except Exception as e:
                if self.logger: self.logger.error(f"Failed to process {fp} for data analysis: {e}")
        
        conn.close()
        
        # 写入元数据
        with open(self.schema_path, 'w', encoding='utf-8') as f:
            json.dump(all_schemas, f, indent=4, ensure_ascii=False)
            
        return all_schemas

    def _sanitize_table_name(self, name: str) -> str:
        # 去除扩展名并保留合法字符
        base = os.path.splitext(name)[0]
        clean = "".join([c if c.isalnum() else "_" for c in base])
        return f"tbl_{clean.lower()}"

    def _extract_df_info(self, df: pd.DataFrame, source_desc: str) -> Dict[str, Any]:
        return {
            "source": source_desc,
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "row_count": len(df),
            "sample_data": df.head(3).to_dict(orient='records')
        }

    def generate_sql_query(self, query: str, model_client) -> str:
        """调用 LLM 根据 Schema 生成 SQL"""
        with open(self.schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
            
        prompt = f"""
你是一名专业的数据分析师。请根据以下数据库结构生成一条标准的 SQLite 查询语句来回答用户的问题。
数据库包含以下表：
{json.dumps(schema, indent=2, ensure_ascii=False)}

要求：
1. 仅返回 SQL 语句，不要有任何其他文字。
2. 确保 SQL 语法符合 SQLite 规范。
3. 如果需要跨表，请使用 JOIN。
4. 字段名请严格对照提供的 Schema。

用户问题：{query}
"""
        # 此处调用实际的 LLM 客户端
        response = model_client.complete(prompt)
        return response.text.strip().replace("```sql", "").replace("```", "")

    def execute_sql(self, sql: str) -> Dict[str, Any]:
        """执行 SQL 并返回结果表格"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(sql, conn)
            conn.close()
            return {
                "success": True,
                "data": df.to_dict(orient='records'),
                "columns": list(df.columns),
                "rows": len(df)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
