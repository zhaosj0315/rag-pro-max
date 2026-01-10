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
        [v3.7.0 企业级升级] 语义化提取：从海量文档中识别表结构及【业务关联图谱】。
        """
        all_text = "\n".join([d.text for d in docs[:30]]) 
        
        prompt = f"""
你是一名资深首席架构师。请从以下文档中提取数据库模型。
文档内容：{all_text}

要求输出标准的 JSON，必须包含：
1. "tables": {{ "表名": {{ "desc": "业务含义", "cols": [{{ "name": "字段名", "type": "类型", "comment": "解释" }}] }} }}
2. "relationships": [ {{ "source": "表A", "target": "表B", "on": "关联字段", "logic": "业务场景" }} ]
3. "business_domains": {{ "领域名": ["相关表名"] }}

即使文档中没有外键约束，也请根据业务常识推断隐含的逻辑关联。
"""
        response = model_client.complete(prompt)
        try:
            content = response.text.strip().replace("```json", "").replace("```", "")
            schema_data = json.loads(content)
            with open(self.schema_path, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, indent=4, ensure_ascii=False)
            return schema_data
        except:
            return {"error": "语义模型解析失败"}

    def infer_business_blueprint(self, schemas: Any, model_client) -> Dict[str, Any]:
        """
        [接口恢复] 业务蓝图推演：对接 v3.7.0 架构图谱引擎。
        """
        try:
            if isinstance(schemas, str):
                schemas_str = schemas
            else:
                schemas_str = json.dumps(schemas, indent=2, ensure_ascii=False, default=str)
            
            prompt = f"""
请根据以下数据库架构图谱推导业务全景图：
{schemas_str}

请输出 JSON：
1. business_scenario: 业务系统描述。
2. core_logic: 核心业务流转逻辑。
3. analysis_dimensions: 推荐的 5 个业务分析维度。
"""
            response = model_client.complete(prompt)
            blueprint = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
            with open(self.blueprint_path, 'w', encoding='utf-8') as f:
                json.dump(blueprint, f, indent=4, ensure_ascii=False)
            return blueprint
        except Exception as e:
            if self.logger: self.logger.error(f"业务蓝图推演失败: {e}")
            return {
                "business_scenario": "自动推演失败",
                "core_logic": "无法识别",
                "analysis_dimensions": ["通用数据分析"],
                "error": str(e)
            }

    def _get_relevant_tables(self, query: str, schemas: Dict[str, Any]) -> List[str]:
        """针对百表规模的动态剪枝"""
        all_tables = schemas.get("tables", {})
        if len(all_tables) <= 8:
            return list(all_tables.keys())
        relevant = []
        query_words = query.lower()
        for t_name, info in all_tables.items():
            if t_name.lower() in query_words or any(w in info.get("desc", "").lower() for w in query_words if len(w)>1):
                relevant.append(t_name)
        rels = schemas.get("relationships", [])
        extra = []
        for r in rels:
            if r["source"] in relevant and r["target"] not in relevant: extra.append(r["target"])
            elif r["target"] in relevant and r["source"] not in relevant: extra.append(r["source"])
        return list(set(relevant + extra))[:10]

    def execute_analysis(self, query: str, model_client, context_text: str = "") -> Dict[str, Any]:
        """
        [v3.7.5 多表穿透版] 支持复杂血缘推理与逻辑透明化
        """
        if not os.path.exists(self.schema_path):
             return {"success": False, "logic": "未找到数据结构定义，请上传文档或表单。"}

        with open(self.schema_path, 'r', encoding='utf-8') as f:
            full_schemas = json.load(f)
        
        # 1. 语义路由：动态筛选相关子集
        relevant_table_names = self._get_relevant_tables(query, full_schemas)
        pruned_schemas = {
            "tables": {name: full_schemas["tables"][name] for name in relevant_table_names if name in full_schemas["tables"]},
            "relationships": [r for r in full_schemas.get("relationships", []) if r["source"] in relevant_table_names or r["target"] in relevant_table_names]
        }
        
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # 2. 逻辑推演：先思考关联路径
        logic_prompt = f"""
你是一名资深数据分析专家。针对以下业务模型和用户问题，请先输出你的【分析路径】。
业务模型：{json.dumps(pruned_schemas, ensure_ascii=False)}
用户问题：{query}

要求：
1. 说明你需要用到哪些表。
2. 说明这些表之间如何通过字段进行联接（JOIN）。
3. 说明你将采取何种统计策略（过滤、分组、聚合）。
请仅输出一小段话，不要输出 SQL。
"""
        analysis_path = ""
        try:
            analysis_path = model_client.complete(logic_prompt).text if hasattr(model_client, 'complete') else model_client.chat(model=model_client.model, messages=[{"role":"user","content":logic_prompt}]).message.content
        except: analysis_path = "自动推导关联逻辑..."

        # 3. 精准 SQL 生成 (基于路径)
        sql_prompt = f"""基于你的分析路径："{analysis_path}"，请编写 SQLite 语句。
可用模型子集：{json.dumps(pruned_schemas, ensure_ascii=False)}
要求：仅返回一条 SQL，包裹在 [SQL_START] 和 [SQL_END] 之间。"""
        
        sql_query = ""
        try:
            res = model_client.complete(sql_prompt).text if hasattr(model_client, 'complete') else model_client.chat(model=model_client.model, messages=[{"role":"user","content":sql_prompt}]).message.content
            if "[SQL_START]" in res:
                sql_query = res.split("[SQL_START]")[1].split("[SQL_END]")[0].strip()
            elif "SELECT" in res.upper():
                import re
                match = re.search(r'```sql\s*(.*?)\s*```', res, re.DOTALL | re.IGNORECASE)
                if match: sql_query = match.group(1).strip()
        except: pass

        # 4. 运行与仿真
        execution_result = {"success": False, "data": []}
        is_simulated = False
        if sql_query:
            try:
                conn = sqlite3.connect(self.db_path)
                if not conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
                    self._recover_data_from_docstore()
                conn.close()
            except: pass
            execution_result = self.execute_sql(sql_query)
            
            if (not execution_result["success"] or not execution_result["data"]):
                is_simulated = True
                sim_prompt = f"""你是一名建模专家。当前处于【架构仿真模式】。
请根据 SQL 逻辑和业务模型，模拟出 5 条极其真实的跨表关联数据。
SQL: {sql_query}
模型: {json.dumps(pruned_schemas, ensure_ascii=False)}
要求：仅输出 JSON 数组。"""
                try:
                    sim_res = model_client.complete(sim_prompt).text if hasattr(model_client, 'complete') else model_client.chat(model=model_client.model, messages=[{"role":"user","content":sim_prompt}]).message.content
                    import re
                    json_match = re.search(r'(\[.*\])', sim_res, re.DOTALL)
                    if json_match:
                        execution_result = {"success": True, "data": json.loads(json_match.group(1))}
                except: pass

        if not execution_result["success"] or not sql_query:
             return {"success": False, "logic": "多表分析推演失败，请检查文档关联说明。"}

        # 5. 准备流式报告 (融入分析逻辑)
        summary_prompt = f"""
你是一名资深商业分析师。请针对以下结果撰写深度报告。
用户问题: {query}
分析路径: {analysis_path}
结果数据: {json.dumps(execution_result['data'][:10], ensure_ascii=False)}

报告要求：
1. 必须解读跨表关联带来的业务价值。
2. 指出数据中的关键趋势或异常。
3. 给出的行动建议必须具有可落地性。

格式：
### 🧭 分析逻辑溯源
(解释为何如此联接数据)

### 💡 核心业务结论
### 📊 数据深度洞察
### 🚀 架构/业务建议
"""
        
        def report_generator():
            if hasattr(model_client, 'stream_chat'):
                from llama_index.core.base.llms.types import ChatMessage, MessageRole
                messages = [ChatMessage(role=MessageRole.USER, content=summary_prompt)]
                try:
                    response_gen = model_client.stream_chat(messages)
                    for chunk in response_gen:
                        if hasattr(chunk, 'delta') and chunk.delta: yield chunk.delta
                        elif hasattr(chunk, 'message') and hasattr(chunk.message, 'content'): yield chunk.message.content
                        else: yield str(chunk)
                except: yield "报告生成异常"
            else:
                res = model_client.complete(summary_prompt).text if hasattr(model_client, 'complete') else model_client.chat(model=model_client.model, messages=[{"role":"user","content":summary_prompt}]).message.content
                for char in res: yield char

        return {
            "sql": sql_query,
            "data": execution_result['data'],
            "logic_gen": report_generator(),
            "analysis_path": analysis_path,
            "success": True,
            "is_simulated": is_simulated
        }

    def _recover_data_from_docstore(self):
        docstore_path = os.path.join(self.kb_path, "docstore.json")
        if not os.path.exists(docstore_path): return
        try:
            with open(docstore_path, 'r', encoding='utf-8') as f:
                docstore = json.load(f)
            nodes = docstore.get("docstore/data", {})
            import io, re
            conn = sqlite3.connect(self.db_path)
            found_data = False
            for node_id, node_data in nodes.items():
                text = node_data.get("__data__", {}).get("text", "")
                metadata = node_data.get("__data__", {}).get("metadata", {})
                file_name = metadata.get("file_name", "")
                if file_name.endswith('.csv') or (',' in text and '\n' in text):
                    table_name = os.path.splitext(file_name)[0] if file_name else f"table_{{node_id[:8]}}"
                    table_name = re.sub(r'[^a-zA-Z0-9_]', '_', table_name)
                    try:
                        df = pd.read_csv(io.StringIO(text))
                        df.to_sql(table_name, conn, index=False, if_exists='replace')
                        found_data = True
                    except: continue
            conn.close()
        except: pass

    def execute_sql(self, sql: str) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            conn.close()
            return {"success": True, "data": rows}
        except Exception as e:
            if self.logger:
                self.logger.error(f"SQL 执行失败: {sql} | Error: {e}")
            return {"success": False, "error": str(e), "data": []}

    def process_files(self, file_paths: List[str]) -> Dict[str, Any]:
        import re
        try:
            if os.path.exists(self.db_path): os.remove(self.db_path)
            conn = sqlite3.connect(self.db_path)
            processed_tables = {}
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                table_name = os.path.splitext(file_name)[0]
                table_name = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5]', '_', table_name)
                if file_path.endswith('.csv'): df = pd.read_csv(file_path)
                elif file_path.endswith(('.xls', '.xlsx')): df = pd.read_excel(file_path)
                else: continue
                df.columns = [re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5]', '_', str(c)) for c in df.columns]
                df.to_sql(table_name, conn, index=False, if_exists='replace')
                processed_tables[table_name] = {
                    "description": f"数据来源: {file_name}",
                    "columns": [{"name": c, "type": str(t)} for c, t in df.dtypes.items()]
                }
            conn.close()
            with open(self.schema_path, 'w', encoding='utf-8') as f:
                json.dump({"tables": processed_tables}, f, indent=4, ensure_ascii=False)
            return {"success": True, "tables": list(processed_tables.keys())}
        except Exception as e:
            if self.logger: self.logger.error(f"文件处理入库失败: {e}")
            return {"success": False, "error": str(e)}
