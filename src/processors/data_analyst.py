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
        [v3.9.5 架构优先版] 支持纯表结构文档的逻辑推演与仿真
        """
        # 1. 动态 Schema 准备
        if not os.path.exists(self.schema_path):
            # 如果没有物理 Schema，尝试从上下文检索信息进行即时建模
            if context_text:
                if self.logger: self.logger.info("🧩 [v3.9.5] 物理模型缺失，启动即时语义建模...")
                # 构造临时 Document 对象供提取
                from llama_index.core import Document
                extracted = self.extract_schema_from_docs([Document(text=context_text)], model_client)
                if "error" in extracted:
                    return {"success": False, "logic": "无法从当前文档中识别业务模型，请确保文档包含字段或表结构说明。"}
            else:
                return {"success": False, "logic": "未找到数据结构定义，请上传技术文档或数据表。"}

        with open(self.schema_path, 'r', encoding='utf-8') as f:
            full_schemas = json.load(f)
        
        # 2. 语义路由：动态筛选相关子集
        relevant_table_names = self._get_relevant_tables(query, full_schemas)
        pruned_schemas = {
            "tables": {name: full_schemas["tables"][name] for name in relevant_table_names if name in full_schemas["tables"]},
            "relationships": [r for r in full_schemas.get("relationships", []) if r["source"] in relevant_table_names or r["target"] in relevant_table_names]
        }
        
        # 3. 逻辑推演路径 (透明化)
        logic_prompt = f"针对业务模型：{json.dumps(pruned_schemas, ensure_ascii=False)}\n用户问题：{query}\n请简述分析逻辑、联接路径和聚合策略。仅输出一小段话。"
        try:
            analysis_path = model_client.complete(logic_prompt).text if hasattr(model_client, 'complete') else model_client.chat(model=model_client.model, messages=[{"role":"user","content":logic_prompt}]).message.content
        except: analysis_path = "自动建立跨表关联逻辑..."

        # 4. 执行与强制仿真
        sql_prompt = f"基于路径：{analysis_path}\n可用表：{json.dumps(pruned_schemas, ensure_ascii=False)}\n用户问题：{query}\n仅返回一条包裹在 [SQL_START] 和 [SQL_END] 之间的 SQLite。"
        sql_query = ""
        try:
            res = model_client.complete(sql_prompt).text if hasattr(model_client, 'complete') else model_client.chat(model=model_client.model, messages=[{"role":"user","content":sql_prompt}]).message.content
            if "[SQL_START]" in res: sql_query = res.split("[SQL_START]")[1].split("[SQL_END]")[0].strip()
            elif "SELECT" in res.upper():
                import re
                match = re.search(r'```sql\s*(.*?)\s*```', res, re.DOTALL | re.IGNORECASE)
                if match: sql_query = match.group(1).strip()
        except: pass

        execution_result = {"success": False, "data": []}
        is_simulated = False
        
        if sql_query:
            # 尝试物理执行
            try:
                conn = sqlite3.connect(self.db_path)
                if not conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
                    self._recover_data_from_docstore()
                conn.close()
                execution_result = self.execute_sql(sql_query)
            except: pass
            
            # [关键改进]：如果执行失败或结果集为空，【强制】启动仿真推演
            if (not execution_result["success"] or not execution_result["data"]):
                is_simulated = True
                if self.logger: self.logger.info("🔮 [v3.9.5] 物理数据缺失，进入‘架构级仿真推演’模式...")
                sim_prompt = f"""
你是一名资深建模专家。当前处于【架构仿真模式】。
数据库中暂无真实数据，请根据【表结构文档】和【SQL逻辑】，模拟出 5 条极其真实的业务数据 JSON。
SQL: {sql_query}
表模型: {json.dumps(pruned_schemas, ensure_ascii=False)}
参考背景: {context_text[:1500]}
请仅输出 JSON 数组。
"""
                try:
                    sim_res = model_client.complete(sim_prompt).text if hasattr(model_client, 'complete') else model_client.chat(model=model_client.model, messages=[{"role":"user","content":sim_prompt}]).message.content
                    import re, json
                    json_match = re.search(r'(\[.*\])', sim_res, re.DOTALL)
                    if json_match:
                        execution_result = {"success": True, "data": json.loads(json_match.group(1))}
                except: pass

        if not execution_result["success"] or not sql_query:
             return {"success": False, "logic": "架构推演受阻，请确保上传了表结构相关的文档。"}

        # 5. 准备流式报告 (融入归因与预测)
        summary_prompt = f"""
你是一名顶级商业决策专家。请针对以下结果撰写【极光分析报告】。
用户问题: {query}
SQL逻辑: {sql_query}
结果数据: {json.dumps(execution_result['data'][:15], ensure_ascii=False)}
注意：这是基于您提供的业务模型进行的【架构级深度推演】。

报告结构（严格执行）：
### 🧭 业务血缘推演
(简述分析路径与联接逻辑)

### 💡 核心结论
(用一句话定调)

### 🔍 异常归因与诊断 (Diagnostic)
(分析数据波动的原因，指出潜在的业务风险或机会点)

### 🔮 趋势预测与建议 (Predictive)
(基于当前数据推演未来的走势，并给出 3 条可落地的商业行动建议)
"""
        
        def report_generator():
            from llama_index.core.base.llms.types import ChatMessage, MessageRole
            messages = [ChatMessage(role=MessageRole.USER, content=summary_prompt)]
            try:
                if hasattr(model_client, 'stream_chat'):
                    response_gen = model_client.stream_chat(messages)
                    for chunk in response_gen:
                        if hasattr(chunk, 'delta') and chunk.delta: yield chunk.delta
                        elif hasattr(chunk, 'message') and hasattr(chunk.message, 'content'): yield chunk.message.content
                        else: yield str(chunk)
                else:
                    res = model_client.complete(summary_prompt).text if hasattr(model_client, 'complete') else model_client.chat(model=model_client.model, messages=[{"role":"user","content":summary_prompt}]).message.content
                    for char in res: yield char
            except: yield "推演报告生成异常"

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
