import os
import json
import pandas as pd
import sqlite3
import re
from typing import List, Dict, Any
from datetime import datetime
import hashlib

class DataAnalystEngine:
    def __init__(self, kb_path: str, logger=None):
        self.kb_path = kb_path
        self.logger = logger
        self.db_path = os.path.join(kb_path, "business_data.db")
        self.schema_path = os.path.join(kb_path, "business_schema.json")
        self.blueprint_path = os.path.join(kb_path, "business_blueprint.json")
        self.memory_path = os.path.join(kb_path, "business_sql_memory.json")

    def _load_memory(self) -> List[Dict]:
        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, 'r', encoding='utf-8') as f: return json.load(f)
            except: pass
        return []

    def _save_memory(self, query: str, sql: str, goal: str):
        try:
            memories = self._load_memory()
            for m in memories:
                if m['query'] == query: return
            memories.append({"query": query, "goal": goal, "sql": sql, "timestamp": datetime.now().isoformat()})
            if len(memories) > 50: memories = memories[-50:]
            with open(self.memory_path, 'w', encoding='utf-8') as f: json.dump(memories, f, indent=2, ensure_ascii=False)
        except: pass

    def extract_schema_from_docs(self, docs: List[Any], model_client, status_callback=None) -> Dict[str, Any]:
        if status_callback: status_callback(f"📄 正在阅读 {len(docs)} 个业务文档...")
        all_text = "\n".join([d.text for d in docs[:30]]) 
        if len(all_text) > 60000: all_text = all_text[:60000] + "..."
        if status_callback: status_callback("🧠 正在请求大模型提取业务架构...")
        prompt = f"你是一名资深架构师。请从以下文档中严谨提取业务模型。\n文档：{all_text}\n要求输出JSON，包含 macro_context, tables (含字段名、注释), relationships, business_domains。"
        response = model_client.complete(prompt)
        try:
            content = response.text.strip()
            json_match = re.search(r'(\{.*\})', content, re.DOTALL)
            if json_match: content = json_match.group(1)
            schema_data = json.loads(content)
            with open(self.schema_path, 'w', encoding='utf-8') as f: json.dump(schema_data, f, indent=4, ensure_ascii=False)
            return schema_data
        except: return {"error": "解析失败"}

    def infer_business_blueprint(self, schemas: Any, model_client) -> Dict[str, Any]:
        try:
            schemas_str = json.dumps(schemas, indent=2, ensure_ascii=False, default=str)[:8000]
            prompt = f"根据以下数据库架构推导业务全景图：\n{schemas_str}\n输出标准JSON：business_scenario, core_logic, analysis_dimensions。"
            response = model_client.complete(prompt)
            content = response.text.strip()
            json_match = re.search(r'(\{.*\})', content, re.DOTALL)
            if json_match: content = json_match.group(1)
            blueprint = json.loads(content)
            with open(self.blueprint_path, 'w', encoding='utf-8') as f: json.dump(blueprint, f, indent=4, ensure_ascii=False)
            return blueprint
        except: return {"business_scenario": "通用业务"}

    def _get_relevant_tables(self, query: str, schemas: Dict[str, Any]) -> List[str]:
        all_tables = schemas.get("tables", {})
        if len(all_tables) <= 8: return list(all_tables.keys())
        relevant = []
        qw = query.lower()
        for t, info in all_tables.items():
            if t.lower() in qw or any(w in str(info.get("desc","")).lower() for w in qw if len(w)>1): relevant.append(t)
        return list(set(relevant))[:10]

    def _ensure_sandbox_ready(self, schemas: Dict[str, Any], model_client, status_callback=None, target_tables: List[str] = None) -> Dict[str, str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS dual (dummy TEXT)")
        cursor.execute("SELECT count(*) FROM dual")
        if cursor.fetchone()[0] == 0: cursor.execute("INSERT INTO dual (dummy) VALUES ('X')")
        
        tables_to_mock = []
        table_mapping = {}
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        physical_tables_lower = {row[0].lower(): row[0] for row in cursor.fetchall()}
        
        def find_physical_match(target):
            t = target.lower()
            if t in physical_tables_lower: return physical_tables_lower[t]
            if t + 's' in physical_tables_lower: return physical_tables_lower[t + 's']
            if t.endswith('s') and t[:-1] in physical_tables_lower: return physical_tables_lower[t[:-1]]
            for k in [f"t_{t}", f"{t}_list", f"{t}_data"]:
                if k in physical_tables_lower: return physical_tables_lower[k]
            return None

        check_list = target_tables if target_tables else list(schemas.get('tables', {}).keys())
        for t_name in check_list:
            if t_name not in schemas.get('tables', {}): continue
            if "." in t_name or t_name.lower().startswith("sqlite_") or t_name.lower() == "dual": continue
            
            p_match = find_physical_match(t_name)
            if p_match:
                try: 
                    if cursor.execute(f"SELECT count(*) FROM {p_match}").fetchone()[0] > 0:
                        table_mapping[t_name] = p_match
                        continue
                except: pass
            tables_to_mock.append(t_name)
        
        if tables_to_mock and model_client:
            if status_callback: status_callback(f"🎲 正在为 {len(tables_to_mock)} 张表生成持久化仿真数据...")
            for idx, t in enumerate(tables_to_mock):
                t_info = schemas['tables'].get(t, {})
                cols = t_info.get('cols', t_info.get('columns', []))
                cols_str = ", ".join([f"{c['name']} (注释: {c.get('comment', '无')})" for c in cols])
                mock_prompt = f"为业务表 {t} 生成 20 条逻辑闭环的 SQL INSERT 语句。\n字段：{cols_str}\n背景：{schemas.get('macro_context')}\n仅输出 SQL，单引号转义。"
                try:
                    mock_sql = model_client.complete(mock_prompt).text
                    cols_def = ", ".join([f"{c['name']} TEXT" for c in cols])
                    cursor.execute(f"CREATE TABLE IF NOT EXISTS {t} ({cols_def})")
                    for line in mock_sql.split(';'):
                        if line.strip().upper().startswith('INSERT'): cursor.execute(line.strip())
                except: pass
        conn.commit()
        conn.close()
        return table_mapping

    def recommend_visualization(self, query: str, columns: List[str], sample_data: List[Dict], model_client) -> Dict[str, Any]:
        prompt = f"专家级可视化推荐。\n问题: {query}\n字段: {columns}\n样本: {json.dumps(sample_data[:2], ensure_ascii=False)}\n输出标准JSON: viz_type, x_axis, y_axis, title, insight(中英双语), reason。"
        try:
            res = model_client.complete(prompt).text
            json_match = re.search(r'(\{.*\})', res, re.DOTALL)
            return json.loads(json_match.group(1)) if json_match else {"viz_type": "table"}
        except: return {"viz_type": "table"}

    def execute_analysis(self, query: str, model_client, context_text: str = "", status_callback=None) -> Dict[str, Any]:
        if status_callback: status_callback("🧠 正在初始化业务语义环境...")
        if not os.path.exists(self.schema_path): return {"success": False, "logic": "未找到数据结构定义。"}
        with open(self.schema_path, 'r', encoding='utf-8') as f: full_schemas = json.load(f)
        
        metadata_keywords = ["有哪些指标", "说明", "字典", "结构", "有哪些表", "模型"]
        if any(k in query for k in metadata_keywords):
            if status_callback: status_callback("📖 正在从元模型中提取业务定义...")
            summary_prompt = f"根据以下模型解答问题: {query}\n模型: {json.dumps(full_schemas, ensure_ascii=False)[:5000]}"
            def metadata_gen():
                for char in model_client.complete(summary_prompt).text: yield char
            return {"stages": [], "logic_gen": metadata_gen(), "success": True, "macro_context": "元数据咨询"}

        rel_tables = self._get_relevant_tables(query, full_schemas)
        table_mapping = self._ensure_sandbox_ready(full_schemas, model_client, status_callback=status_callback, target_tables=rel_tables)
        
        mapped_tables = list(set([table_mapping.get(t, t) for t in rel_tables]))
        corrected_schemas = {"tables": {table_mapping.get(t, t): info for t, info in full_schemas['tables'].items()}, "macro_context": full_schemas.get("macro_context", "")}
        pruned_schemas = {"macro_context": corrected_schemas["macro_context"], "tables": {t: corrected_schemas["tables"].get(t) for t in mapped_tables if t in corrected_schemas["tables"]}}

        if status_callback: status_callback("🎯 正在拆解战略目标与分析路径...")
        decomp_prompt = f"你是顾问。将需求 {query} 拆解为 2-3 个逻辑递进的分析阶段。\n模型：{json.dumps(pruned_schemas, ensure_ascii=False)}\n要求返回标准JSON数组: [{{stage_id, title, transformation, goal, logic}}]"
        try:
            res = model_client.complete(decomp_prompt).text
            stages_meta = json.loads(re.search(r'(\[.*\])', res, re.DOTALL).group(1))
        except: stages_meta = [{"stage_id": 1, "title": "全量数据分析", "transformation": "执行数据透视"}]

        final_stages_data = []
        full_analysis_context = ""

        for i, meta in enumerate(stages_meta):
            if status_callback: status_callback(f"⚙️ [Stage {i+1}] 正在构建 SQL 逻辑...")
            
            # 样本注入
            sample_context = ""
            for t in mapped_tables:
                s_res = self.execute_sql(f"SELECT * FROM {t} LIMIT 2")
                if s_res["success"] and s_res["data"]:
                    sample_context += f"- 表 '{t}' 样例: {json.dumps(s_res['data'], ensure_ascii=False)}\n"

            # 字段剪枝逻辑
            sub_schema = {}
            for t in mapped_tables:
                info = corrected_schemas['tables'].get(t, {})
                all_cols = info.get('cols', info.get('columns', []))
                # 简单过滤核心字段
                core_keys = ['id', 'name', 'date', 'amount', 'price', 'total', 'status', 'type', 'user', 'order', '金额', '时间', '日期']
                filtered = [c for c in all_cols if any(k in c['name'].lower() or k in str(c.get('comment','')).lower() for k in core_keys)]
                sub_schema[t] = {"desc": info.get("desc"), "cols": filtered if filtered else all_cols[:8]}

            sql_prompt = f"""基于路径 "{meta.get('transformation')}" 编写 SQL。
业务背景：{pruned_schemas['macro_context']}
精简模型：{json.dumps(sub_schema, ensure_ascii=False)}
数据样例：{sample_context}
前序结论：{full_analysis_context}

【强制输出格式】: 返回一个标准 JSON 对象，严禁包含其他文字：
{{
  "dataworks": "MaxCompute SQL (含 ${{bizdate}})",
  "standard": "ANSI SQL",
  "sqlite": "SQLite SQL"
}}
"""
            sqls = {"sqlite": ""}
            try:
                res_text = model_client.complete(sql_prompt).text
                match = re.search(r'(\{.*\})', res_text, re.DOTALL)
                if match: sqls = json.loads(match.group(1))
            except: pass

            if status_callback: status_callback(f"🧪 [Stage {i+1}] 执行验证中...")
            exec_res = {"success": False, "data": []}
            if sqls.get("sqlite"):
                exec_res = self.execute_sql(sqls["sqlite"], model_client=model_client)
                if exec_res["success"]:
                    if status_callback: status_callback(f"⚡ [Stage {i+1}] SQL 执行成功，获取 {len(exec_res['data'])} 行数据")
                    if len(exec_res['data']) > 0: self._save_memory(query=query, sql=sqls["sqlite"], goal=meta['title'])
            
            # 可视化预推荐
            recommendation = {"viz_type": "table"}
            if exec_res["success"] and exec_res["data"]:
                recommendation = self.recommend_visualization(meta['title'], list(exec_res["data"][0].keys()), exec_res["data"], model_client)

            stage_entry = {"meta": meta, "sqls": sqls, "data": exec_res["data"], "recommendation": recommendation}
            final_stages_data.append(stage_entry)
            full_analysis_context += f"阶段 {i+1} 结论: {json.dumps(exec_res['data'][:2], ensure_ascii=False)}\n"

        if status_callback: status_callback("📝 正在撰写战略分析报告...")
        summary_prompt = f"基于以下推演结果撰写 SCQA 战略报告。\n问题: {query}\n结果: {full_analysis_context}\n要求: 结论先行，Bento Grid 风格。"
        
        def report_gen():
            if hasattr(model_client, 'stream_chat'):
                from llama_index.core.base.llms.types import ChatMessage, MessageRole
                try:
                    for chunk in model_client.stream_chat([ChatMessage(role=MessageRole.USER, content=summary_prompt)]):
                        yield chunk.delta if hasattr(chunk, 'delta') else str(chunk)
                except: yield "报告生成异常"
            else:
                for char in model_client.complete(summary_prompt).text: yield char

        def make_json_safe(obj):
            if isinstance(obj, list): return [make_json_safe(i) for i in obj]
            if isinstance(obj, dict): return {k: make_json_safe(v) for k, v in obj.items()}
            import pandas as pd
            import numpy as np
            if obj is None or pd.isna(obj): return None
            if isinstance(obj, (pd.Timestamp, datetime)): return obj.strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(obj, (int, np.integer)): return int(obj)
            if isinstance(obj, (float, np.floating)): return float(obj)
            return str(obj) if not isinstance(obj, (str, bool)) else obj

        return {"stages": make_json_safe(final_stages_data), "logic_gen": report_gen(), "success": True, "macro_context": pruned_schemas['macro_context']}

    def _recover_data_from_docstore(self):
        try:
            docstore_path = os.path.join(self.kb_path, "docstore.json")
            if not os.path.exists(docstore_path): return
            with open(docstore_path, 'r', encoding='utf-8') as f: docstore = json.load(f)
            nodes = docstore.get("docstore/data", {})
            conn = sqlite3.connect(self.db_path)
            for node_id, node_data in nodes.items():
                text = node_data.get("__data__", {}).get("text", "")
                metadata = node_data.get("__data__", {}).get("metadata", {})
                file_name = metadata.get("file_name", "")
                if file_name.endswith('.csv') or (',' in text and '\n' in text):
                    t_name = re.sub(r'[^a-zA-Z0-9_]', '_', os.path.splitext(file_name)[0] if file_name else f"table_{node_id[:8]}")
                    try: pd.read_csv(pd.io.common.StringIO(text)).to_sql(t_name, conn, index=False, if_exists='replace')
                    except: continue
            conn.close()
        except: pass

    def execute_sql(self, sql: str, model_client=None) -> Dict[str, Any]:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=30)
                conn.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
                cursor = conn.cursor()
                clean_sql = sql.replace('\\
', ' ').replace('\\', '')
                statements = [s.strip() for s in clean_sql.split(';') if s.strip()]
                rows = []
                for idx, stmt in enumerate(statements):
                    try:
                        cursor.execute(stmt)
                        if stmt.upper().startswith("SELECT"): rows = cursor.fetchall()
                    except Exception as e:
                        if model_client:
                            fix_prompt = f"Fix SQLite error: {e}\nSQL: {stmt}\nOutput ONLY the corrected SQL."
                            try:
                                fixed = re.sub(r'```sql|```', '', model_client.complete(fix_prompt).text.strip(), flags=re.I).strip()
                                cursor.execute(fixed)
                                if fixed.upper().startswith("SELECT"): rows = cursor.fetchall()
                                continue
                            except: raise e
                        raise e
                conn.commit()
                conn.close()
                return {"success": True, "data": rows}
            except Exception as e:
                if attempt < max_retries - 1 and "locked" in str(e).lower():
                    import time; time.sleep(0.5); continue
                if "no such table" in str(e).lower():
                    self._recover_data_from_docstore()
                return {"success": False, "error": str(e), "data": []}
        return {"success": False, "error": "Max retries", "data": []}

    def process_files(self, file_paths: List[str], model_client=None, status_callback=None) -> Dict[str, Any]:
        import re
        try:
            if os.path.exists(self.db_path): os.remove(self.db_path)
            conn = sqlite3.connect(self.db_path)
            physical_tables = {}
            semantic_docs = []
            if status_callback: status_callback(f"📊 正在处理 {len(file_paths)} 个源材料...")
            for file_path in file_paths:
                file_name = os.path.basename(file_path).lower()
                if file_name.endswith(('.md', '.markdown', '.pdf', '.docx', '.txt')):
                    semantic_docs.append(file_path); continue
                t_name = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5]', '_', os.path.splitext(file_name)[0])
                try:
                    df = pd.read_csv(file_path) if file_name.endswith('.csv') else pd.read_excel(file_path)
                    df.columns = [re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5]', '_', str(c)) for c in df.columns]
                    df.to_sql(t_name, conn, index=False, if_exists='replace')
                    row_count = conn.execute(f"SELECT count(*) FROM {t_name}").fetchone()[0]
                    if status_callback: status_callback(f"✅ 表 '{t_name}' 导入成功 ({row_count} 行)")
                    physical_tables[t_name] = {"source": file_name, "cols": [{"name": c, "type": str(t)} for c, t in df.dtypes.items()]}
                except: pass
            conn.close()
            modeling_summary = "电商全链路运营分析"
            if model_client and physical_tables:
                try: modeling_summary = model_client.complete(f"概括核心业务逻辑：{json.dumps(physical_tables, ensure_ascii=False)}").text.strip()
                except: pass
                if status_callback: status_callback(f"🧠 建模逻辑: {modeling_summary}")
            unified_schema = {"tables": physical_tables, "macro_context": modeling_summary, "relationships": []}
            if semantic_docs and model_client:
                docs_content = []
                for doc_path in semantic_docs:
                    with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f: docs_content.append(f.read()[:5000])
                try:
                    res = model_client.complete(f"构建模型。物理表：{json.dumps(physical_tables, ensure_ascii=False)}\n材料：{''.join(docs_content)}").text
                    match = re.search(r'(\{.*\})', res, re.DOTALL)
                    if match:
                        semantic = json.loads(match.group(1))
                        for t, info in semantic.get('tables', {}).items():
                            if t in unified_schema['tables']: unified_schema['tables'][t].update(info); unified_schema['tables'][t]['is_virtual'] = False
                            else: unified_schema['tables'][t] = info; unified_schema['tables'][t]['is_virtual'] = True
                        unified_schema['macro_context'] = semantic.get('macro_context', unified_schema['macro_context'])
                        unified_schema['relationships'] = semantic.get('relationships', [])
                except: pass
            with open(self.schema_path, 'w', encoding='utf-8') as f: json.dump(unified_schema, f, indent=4, ensure_ascii=False)
            if model_client:
                if status_callback: status_callback("🧪 正在执行出厂级高保真数据预填充...")
                self._ensure_sandbox_ready(unified_schema, model_client, status_callback=None)
            if status_callback: status_callback(f"✅ 全域建模完成，数据已固化至数据库")
            return {"success": True, "tables": list(unified_schema['tables'].keys())}
        except Exception as e: return {"success": False, "error": str(e)}