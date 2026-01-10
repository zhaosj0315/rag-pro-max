import json
import pandas as pd
import sqlite3
import re
from typing import Dict, Any, List

class DataAnalystV7:
    def __init__(self, llm_client=None):
        self.llm = llm_client
        # 内存数据库，模拟隔离环境
        self.conn = sqlite3.connect(":memory:") 
        self.cursor = self.conn.cursor()
        
    def step1_etl_ingestion(self, file_path: str = None, mock_df: pd.DataFrame = None, table_name: str = "raw_data") -> str:
        """
        阶段1: 数据入库 (ETL)
        简单模拟：将 DataFrame 清洗并入库
        """
        df = mock_df
        
        # 1. 模拟清洗：标准化列名 (中文 -> 英文)
        # 在真实场景中这里会调用 LLM，这里简化为规则
        # 假设 df 已经是清洗过的或英文列名，或者我们做一个简单的映射演示
        cleaned_columns = {}
        for col in df.columns:
            # 简单去除非法字符
            clean_col = re.sub(r'[^a-zA-Z0-9_]', '_', col).lower()
            cleaned_columns[col] = clean_col
        
        df = df.rename(columns=cleaned_columns)
        
        # 2. 入库
        df.to_sql(table_name, self.conn, index=False, if_exists='replace')
        return table_name

    def step2_schema_modeling(self, table_names: List[str]) -> Dict[str, Any]:
        """
        阶段2: 语义建模 (Schema & Relationship)
        核心：提取表结构并推导关联
        """
        schemas = {}
        
        # 1. 提取基础 Schema
        for table in table_names:
            self.cursor.execute(f"PRAGMA table_info({table})")
            columns = self.cursor.fetchall()
            # 格式: (cid, name, type, notnull, dflt_value, pk)
            col_info = [{"name": c[1], "type": c[2]} for c in columns]
            
            # 数据采样 (Profile)
            df = pd.read_sql(f"SELECT * FROM {table} LIMIT 3", self.conn)
            sample = df.to_dict(orient='records')
            
            schemas[table] = {
                "columns": col_info,
                "sample_data": sample
            }
            
        # 2. 模拟 LLM 推导关联关系 (Mock LLM response for logic test)
        # 在真实场景中，这里发送 Prompt 给 LLM
        relationships = self._mock_llm_relationship_inference(schemas)
        
        return {
            "tables": schemas,
            "relationships": relationships
        }

    def step3_business_inference(self, schema_model: Dict[str, Any]) -> Dict[str, Any]:
        """
        阶段3: 业务逻辑识别 (Business Inference)
        """
        # 模拟 LLM 识别业务场景
        # Prompt: "基于这些表结构，这是什么业务？核心指标是什么？"
        blueprint = self._mock_llm_business_inference(schema_model)
        return blueprint

    def step4_execution_and_insight(self, user_query: str, schema_model: Dict, blueprint: Dict) -> Dict[str, Any]:
        """
        阶段4: 生成查询与建议 (Query & Insight)
        """
        # 1. SQL 生成
        sql = self._mock_llm_sql_gen(user_query, schema_model)
        
        # 2. 执行
        try:
            result_df = pd.read_sql(sql, self.conn)
            data_result = result_df.to_dict(orient='records')
        except Exception as e:
            return {"error": str(e)}
            
        # 3. 洞察生成
        insight = self._mock_llm_insight_gen(user_query, data_result, blueprint)
        
        return {
            "sql": sql,
            "data": data_result,
            "insight": insight
        }

    # --- Mock LLM Helpers (为了测试逻辑通畅性，模拟 LLM 的智能输出) ---
    
    def _mock_llm_relationship_inference(self, schemas):
        # 简单规则：如果表A有 user_id，表B也有 user_id，则关联
        rels = []
        keys = {}
        for t, info in schemas.items():
            for col in info['columns']:
                cname = col['name']
                if cname.endswith('_id'):
                    if cname not in keys: keys[cname] = []
                    keys[cname].append(t)
        
        for key, tables in keys.items():
            if len(tables) > 1:
                rels.append(f"{tables[0]}.{key} <-> {tables[1]}.{key}")
        return rels

    def _mock_llm_business_inference(self, schema_model):
        tables = schema_model['tables'].keys()
        if "orders" in tables and "users" in tables:
            return {
                "scenario": "电商零售 (E-commerce)",
                "metrics": ["GMV (总交易额)", "AOV (客单价)", "User Retention (留存率)"]
            }
        return {"scenario": "通用数据", "metrics": ["Count", "Sum"]}

    def _mock_llm_sql_gen(self, query, schema_model):
        # 简单的关键词匹配模拟 SQL 生成
        if "总销售额" in query or "GMV" in query:
            return "SELECT SUM(amount) as total_gmv FROM orders"
        if "用户" in query and "消费" in query:
            return """
            SELECT u.name, SUM(o.amount) as spent 
            FROM users u 
            JOIN orders o ON u.user_id = o.user_id 
            GROUP BY u.name 
            ORDER BY spent DESC
            """
        return "SELECT * FROM orders LIMIT 5"

    def _mock_llm_insight_gen(self, query, data, blueprint):
        # 模拟生成建议
        if not data: return "无数据，无法分析。"
        
        scenario = blueprint['scenario']
        if "spent" in data[0]:
            top_user = data[0]['name']
            top_spend = data[0]['spent']
            return f"【核心发现】: 用户 '{top_user}' 是消费冠军，贡献了 {top_spend} 元。\n【行动建议】: 基于{scenario}场景，建议将该用户升级为 VIP 客户，并推送高客单价商品。"
        
        if "total_gmv" in data[0]:
            return f"【核心发现】: 当前总 GMV 为 {data[0]['total_gmv']} 元。\n【行动建议】: 对比目标 KPI，建议关注转化率漏斗。"
            
        return "数据正常。"
