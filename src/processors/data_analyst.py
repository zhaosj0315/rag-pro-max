import os
import json
import pandas as pd
import sqlite3
import re
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
        [Phase 2: 语义建模]
        从文档中提取 Schema 并推导 ER 关联关系。
        """
        print(f"\n[DA DEBUG] >>> 开始提取 Schema, 文档片段数: {len(docs)}")
        try:
            # 1. 准备上下文 (合并前 20 个片段)
            all_text = "\n".join([d.text for d in docs[:20] if hasattr(d, 'text') and d.text])
            
            if not all_text.strip():
                print("[DA DEBUG] !!! 警告: 文档内容为空，无法提取 Schema")
                return {"error": "empty_content"}

            prompt = f"""
你是一名资深数据库架构师。请分析以下内容，识别出数据库表结构及其关联关系（外键）。

内容摘要：
{all_text[:3500]}

要求：
1. 识别表名、字段名、类型。
2. 识别表间关联 (如 Orders.user_id -> Users.user_id)。
3. 必须输出标准 JSON 格式。

输出示例：
{{
  "tables": {{ "Users": {{ "description": "用户表", "columns": [...] }} }},
  "relationships": ["Users.user_id -> Orders.user_id"]
}}
请仅输出 JSON。
"""
            print("[DA DEBUG] 正在请求 LLM 提取 Schema...")
            response = model_client.complete(prompt)
            raw_text = response.text.strip()
            print(f"[DA DEBUG] LLM 响应内容: {raw_text[:200]}...")
            
            # 使用正则暴力提取 JSON 块
            json_str = raw_text
            json_match = re.search(r'(\{.*\})', raw_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            
            schema_data = json.loads(json_str)
            print(f"[DA DEBUG] ✅ Schema 解析成功: 识别到 {len(schema_data.get('tables', {}))} 张表")
            
            # 持久化
            os.makedirs(self.kb_path, exist_ok=True)
            with open(self.schema_path, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, indent=4, ensure_ascii=False)
            print(f"[DA DEBUG] ✅ Schema 已保存至: {self.schema_path}")
            
            # 自动构建数据库
            self._auto_build_db_from_csv()
                
            return schema_data
        except Exception as e:
            print(f"[DA DEBUG] ❌ Schema 提取失败: {e}")
            return {"error": str(e), "tables": {}, "relationships": []}

    def infer_business_blueprint(self, schemas: Any, model_client) -> Dict[str, Any]:
        """
        [Phase 3: 业务推演]
        基于 Schema 推导业务场景和 KPI。
        """
        print("\n[DA DEBUG] >>> 开始业务蓝图推演...")
        try:
            # 安全序列化
            if isinstance(schemas, str):
                schemas_str = schemas
            else:
                schemas_str = json.dumps(schemas, indent=2, ensure_ascii=False, default=str)
            
            prompt = f"""
请根据以下数据库结构推导业务全景图：
{schemas_str}

请推演并输出 JSON：
{{
  "business_scenario": "业务场景描述",
  "core_logic": "业务流转逻辑",
  "metrics": [
    {{"name": "指标", "definition": "逻辑"}}
  ]
}}
请仅输出 JSON。
"""
            response = model_client.complete(prompt)
            raw_text = response.text.strip()
            
            json_str = raw_text
            json_match = re.search(r'(\{.*\})', raw_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                
            blueprint = json.loads(json_str)
            print(f"[DA DEBUG] ✅ 业务识别成功: {blueprint.get('business_scenario')}")
            
            with open(self.blueprint_path, 'w', encoding='utf-8') as f:
                json.dump(blueprint, f, indent=4, ensure_ascii=False)
                
            return blueprint
        except Exception as e:
            print(f"[DA DEBUG] ❌ 业务推演失败: {e}")
            return {"business_scenario": "通用数据分析", "core_logic": "未知", "metrics": []}

    def execute_analysis(self, query: str, model_client) -> Dict[str, Any]:
        """
        [Phase 4: 执行与决策]
        Query -> SQL -> Execution -> Insight
        """
        print(f"\n[DA DEBUG] >>> 收到分析请求: {query}")
        # 1. 加载上下文
        schemas = {}
        blueprint = {}
        try:
            if os.path.exists(self.schema_path):
                with open(self.schema_path, 'r', encoding='utf-8') as f: schemas = json.load(f)
            if os.path.exists(self.blueprint_path):
                with open(self.blueprint_path, 'r', encoding='utf-8') as f: blueprint = json.load(f)
        except: pass
        
        # 2. 生成 SQL
        rel_hint = "\n".join(schemas.get("relationships", []))
        sql_prompt = f"""
你是一名资深数据分析专家。请基于以下结构生成 SQLite 查询语句。

【表结构】：{json.dumps(schemas.get('tables', {}), ensure_ascii=False)}
【关联关系】：{rel_hint}

用户问题：{query}

要求：
1. 必须使用标准 SQL。
2. 优先使用 GROUP BY 语句以展示数据的分布对比（除非用户明确要求单条记录）。
3. 结果包裹在 [SQL_START] 和 [SQL_END] 之间。
"""
        print("[DA DEBUG] 正在生成 SQL...")
        sql_res = model_client.complete(sql_prompt).text
        sql_query = ""
        if "[SQL_START]" in sql_res:
            sql_query = sql_res.split("[SQL_START]")[1].split("[SQL_END]")[0].strip()
        
        # 3. 执行 SQL
        execution_result = {"success": False, "data": [], "error": None}
        if sql_query:
            execution_result = self.execute_sql(sql_query)
        
        # 4. 生成洞察
        if execution_result['success']:
            data_sample = execution_result['data'][:20] 
            insight_prompt = f"""
作为首席业务分析师，请根据数据结果回答用户问题。

【用户问题】：{query}
【数据结果】：{json.dumps(data_sample, ensure_ascii=False)}

请输出简洁的报告 (Markdown)：
1. **💡 核心结论**: 一句话直接回答提问。
2. **📊 数据解读**: 简要分析数据中的关键点。
3. **🚀 行动建议**: 给出 1-2 条建议。
"""
            print("[DA DEBUG] 正在生成业务洞察报告...")
            final_report = model_client.complete(insight_prompt).text
        else:
            final_report = f"执行失败：{execution_result.get('error')}"

        return {
            "sql": sql_query,
            "data": execution_result.get('data', []),
            "logic": final_report,
            "success": execution_result.get('success', False)
        }

    def execute_sql(self, sql: str) -> Dict[str, Any]:
        """执行 SQL 并返回结果"""
        print(f"[DA DEBUG] 执行 SQL: {sql}")
        try:
            if not os.path.exists(self.db_path):
                self._auto_build_db_from_csv()
            
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            conn.close()
            
            print(f"[DA DEBUG] ✅ 查询完成，返回 {len(rows)} 行")
            return {"success": True, "data": rows}
        except Exception as e:
            print(f"[DA DEBUG] ❌ SQL 错误: {e}")
            return {"success": False, "error": str(e), "data": []}

    def _auto_build_db_from_csv(self):
        """物理构建 SQLite 数据库"""
        print("[DA DEBUG] 正在同步构建 SQLite 数据库...")
        try:
            from src.config.manifest_manager import ManifestManager
            manifest = ManifestManager.load(self.kb_path)
            files_count = 0
            for f_info in manifest.get('files', []):
                f_path = f_info.get('file_path')
                if f_path and os.path.exists(f_path) and f_path.endswith('.csv'):
                    t_name = os.path.splitext(f_info['name'])[0].replace('.', '_')
                    df = pd.read_csv(f_path)
                    conn = sqlite3.connect(self.db_path)
                    df.to_sql(t_name, conn, index=False, if_exists='replace')
                    conn.close()
                    files_count += 1
            print(f"[DA DEBUG] ✅ 数据库就绪，导入 {files_count} 张表")
        except Exception as e:
            print(f"[DA DEBUG] ❌ 物理入库失败: {e}")

    def process_files(self, file_paths: List[str]):
        self._auto_build_db_from_csv()
