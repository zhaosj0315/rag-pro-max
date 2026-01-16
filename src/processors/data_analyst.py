import os
import json
import pandas as pd
import sqlite3
import re
from typing import List, Dict, Any, Optional
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
            if any(m['query'] == query for m in memories): return
            memories.append({"query": query, "goal": goal, "sql": sql, "timestamp": datetime.now().isoformat()})
            with open(self.memory_path, 'w', encoding='utf-8') as f: json.dump(memories[-50:], f, indent=2, ensure_ascii=False)
        except: pass

    def _get_relevant_tables(self, query: str, schemas: Dict[str, Any]) -> List[str]:
        all_tables = schemas.get("tables", {})
        if len(all_tables) <= 3: return list(all_tables.keys())
        relevant = []
        qw = query.lower()
        for t, info in all_tables.items():
            if t.lower() in qw or any(w in str(info.get("desc","")).lower() for w in qw if len(w)>1):
                relevant.append(t)
        # 如果没搜到，默认给前3张 (防止上下文全空)
        return list(set(relevant))[:8] if relevant else list(all_tables.keys())[:3]

    def _ensure_sandbox_ready(self, schemas: Dict[str, Any], model_client, status_callback=None, target_tables: List[str] = None) -> Dict[str, str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS dual (dummy TEXT)")
        if not cursor.execute("SELECT count(*) FROM dual").fetchone()[0]:
            cursor.execute("INSERT INTO dual VALUES ('X')")
        
        table_mapping = {}
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        real_tables = {row[0].lower(): row[0] for row in cursor.fetchall()}
        
        def find_match(name):
            n = name.lower()
            if n in real_tables: return real_tables[n]
            if n + 's' in real_tables: return real_tables[n+'s']
            if n.endswith('s') and n[:-1] in real_tables: return real_tables[n[:-1]]
            for k in [f"t_{n}", f"{n}_info"]:
                if k in real_tables: return real_tables[k]
            return None

        check_list = target_tables if target_tables else list(schemas.get('tables', {}).keys())
        tables_to_mock = []
        for t in check_list:
            if t.lower() in ('dual', 'sqlite_sequence') or "." in t: continue
            match = find_match(t)
            if match:
                try: 
                    if cursor.execute(f"SELECT count(*) FROM {match}").fetchone()[0] > 0:
                        table_mapping[t] = match
                        continue
                except: pass
            tables_to_mock.append(t)

        if tables_to_mock and model_client:
            if status_callback: status_callback(f"🎲 正在初始化 {len(tables_to_mock)} 个扩展维度...")
            for t in tables_to_mock:
                info = schemas['tables'].get(t, {})
                cols = info.get('cols', info.get('columns', []))
                cols_str = ", ".join([f"{c['name']} ({c.get('comment','')})" for c in cols])
                prompt = f"为业务表 {t} 生成 20 条逻辑闭环的 SQL INSERT 语句。\n字段：{cols_str}\n背景：{schemas.get('macro_context')}\n要求：仅输出 SQL，单引号转义，不含 Markdown。"
                try:
                    res = model_client.complete(prompt).text
                    cursor.execute(f"CREATE TABLE IF NOT EXISTS {t} ({', '.join([f'{c['name']} TEXT' for c in cols])})")
                    for line in res.split(';'):
                        clean = line.strip()
                        if clean.upper().startswith('INSERT'): cursor.execute(clean)
                except: pass
        conn.commit()
        conn.close()
        return table_mapping

    def _extract_json(self, text: str) -> Optional[Dict]:
        """[v6.7.1] 强力 JSON 提取器：支持清理多余字符与自动闭合"""
        try:
            # 1. 尝试标准正则
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                clean_json = match.group(1)
                # 处理常见的非法转义
                clean_json = clean_json.replace('\\n', ' ').replace('\\t', ' ')
                return json.loads(clean_json)
        except: pass
        
        # 2. 深度清理模式
        try:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
        except: pass
        return None

    def execute_analysis(self, query: str, model_client, context_text: str = "", status_callback=None) -> Dict[str, Any]:
        if not os.path.exists(self.schema_path): return {"success": False, "logic": "未找到数据定义"}
        with open(self.schema_path, 'r', encoding='utf-8') as f: full_schemas = json.load(f)
        
        # 1. 元数据直查
        if any(k in query for k in ["有哪些指标", "说明", "字典", "结构", "有哪些表"]):
            if status_callback: status_callback("📖 正在检索业务元模型定义...")
            prompt = f"根据以下模型解答问题: {query}\n模型内容: {json.dumps(full_schemas, ensure_ascii=False)[:5000]}"
            def gen():
                for char in model_client.complete(prompt).text: yield char
            return {"stages": [], "logic_gen": gen(), "success": True, "macro_context": "元数据查询"}

        # 2. 相关性裁剪与对齐
        rel_tables = self._get_relevant_tables(query, full_schemas)
        mapping = self._ensure_sandbox_ready(full_schemas, model_client, status_callback, rel_tables)
        
        # 3. 任务拆解
        sub_schema = {mapping.get(t, t): full_schemas['tables'][t] for t in rel_tables if t in full_schemas['tables']}
        decomp_prompt = f"你是一名数据顾问。将需求 {query} 拆解为 2-3 个 SQL 分析阶段。\n模型：{json.dumps(sub_schema, ensure_ascii=False)}\n要求：返回标准 JSON 数组 [{{stage_id, title, transformation, goal}} ]"
        try:
            res = model_client.complete(decomp_prompt).text
            m = re.search(r'(\[.*\])', res, re.DOTALL)
            stages_meta = json.loads(m.group(1)) if m else []
        except: stages_meta = []
        
        if not stages_meta:
            stages_meta = [{"stage_id": 1, "title": "深度数据探索", "transformation": "全量数据聚合查询"}]

        final_data = []
        analysis_context = ""
        
        for i, meta in enumerate(stages_meta):
            if status_callback: status_callback(f"⚙️ [Stage {i+1}] 构建 SQL 推演逻辑...")
            
            # 字段白名单保护
            t_context = {}
            for t in sub_schema:
                info = sub_schema[t]
                cols = info.get('cols', info.get('columns', []))
                keep = ['status', 'state', 'date', 'time', 'amount', 'price', 'total', 'id', 'name', '状态', '日期', '金额']
                filtered = [c for c in cols if any(k in c['name'].lower() or k in str(c.get('comment','')).lower() for k in keep)]
                t_context[t] = {"desc": info.get("desc"), "cols": filtered if filtered else cols[:10]}
                
                # 样本探测
                try:
                    r = self.execute_sql(f"SELECT * FROM {t} LIMIT 1")
                    if r["success"] and r["data"]:
                        t_context[t]["sample"] = r['data'][0]
                except: pass

            sql_prompt = f"""编写分析 SQL。任务: {meta.get('transformation')}
业务背景: {full_schemas.get('macro_context')}
数据模型: {json.dumps(t_context, ensure_ascii=False)}
前序发现: {analysis_context}

要求：必须返回标准 JSON，不要包含 Markdown 装饰。
{{
  "sqlite": "面向 SQLite 的执行 SQL",
  "standard": "标准 ANSI SQL",
  "dataworks": "MaxCompute SQL (含 bizdate)"
}}
"""
            sqls = {"sqlite": ""}
            try:
                raw_res = model_client.complete(sql_prompt).text
                sqls = self._extract_json(raw_res) or {"sqlite": ""}
            except: pass

            if status_callback: status_callback(f"🧪 [Stage {i+1}] 正在执行逻辑验证...")
            exec_res = {"success": False, "data": []}
            if sqls.get("sqlite"):
                exec_res = self.execute_sql(sqls["sqlite"], model_client)
                if exec_res["success"] and exec_res["data"]:
                    if status_callback: status_callback(f"✅ 命中 {len(exec_res['data'])} 行数据")
                    analysis_context += f"阶段{i+1}数据摘录: {json.dumps(exec_res['data'][:1], ensure_ascii=False)}\n"
            
            final_data.append({"meta": meta, "sqls": sqls, "data": exec_res["data"]})

        # 4. 生成报告
        def report_gen():
            p = f"撰写战略报告。需求: {query}\n执行结果: {analysis_context}\n要求: SCQA 架构，结论先行，Bento Grid 风格。"
            if hasattr(model_client, 'stream_chat'):
                from llama_index.core.base.llms.types import ChatMessage, MessageRole
                try:
                    for chunk in model_client.stream_chat([ChatMessage(role=MessageRole.USER, content=p)]):
                        yield chunk.delta if hasattr(chunk, 'delta') else str(chunk)
                except: yield "报告生成中断"
            else: yield model_client.complete(p).text

        return {"stages": final_data, "logic_gen": report_gen(), "success": True, "macro_context": full_schemas.get('macro_context','')}

    def execute_sql(self, sql: str, model_client=None) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
            cursor = conn.cursor()
            # 清理 SQL
            clean_sql = sql.replace('\\
', ' ').replace('```sql', '').replace('```', '').strip()
            statements = [s.strip() for s in clean_sql.split(';') if s.strip()]
            rows = []
            for stmt in statements:
                if not stmt: continue
                try:
                    cursor.execute(stmt)
                    if stmt.upper().startswith("SELECT"): rows = cursor.fetchall()
                except Exception as e:
                    if model_client and stmt.upper().startswith("SELECT"):
                        fix = model_client.complete(f"修正此 SQLite 语法错误: {e}\n错误 SQL: {stmt}\n仅输出修正后的一条 SQL").text
                        fixed_stmt = fix.replace('```sql', '').replace('```', '').strip()
                        cursor.execute(fixed_stmt)
                        rows = cursor.fetchall()
            conn.commit()
            conn.close()
            return {"success": True, "data": rows}
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}

    def process_files(self, file_paths: List[str], model_client=None, status_callback=None) -> Dict[str, Any]:
        try:
            if os.path.exists(self.db_path): os.remove(self.db_path)
            conn = sqlite3.connect(self.db_path)
            physical_tables = {}
            semantic_docs = []
            if status_callback: status_callback(f"📊 解析 {len(file_paths)} 个业务材料...")
            for path in file_paths:
                name = os.path.basename(path).lower()
                if name.endswith(('.md', '.pdf', '.docx', '.txt')):
                    semantic_docs.append(path); continue
                t_name = re.sub(r'[^a-zA-Z0-9_]', '_', os.path.splitext(name)[0])
                try:
                    df = pd.read_csv(path) if name.endswith('.csv') else pd.read_excel(path)
                    df.columns = [re.sub(r'[^a-zA-Z0-9_]', '_', str(c)) for c in df.columns]
                    df.to_sql(t_name, conn, index=False, if_exists='replace')
                    count = conn.execute(f"SELECT count(*) FROM {t_name}").fetchone()[0]
                    if status_callback: status_callback(f"✅ 表 '{t_name}' 物理就绪 ({count} 行)")
                    physical_tables[t_name] = {"cols": [{"name": c, "type": str(t)} for c, t in df.dtypes.items()]}
                except: pass
            conn.close()
            modeling_summary = "多维业务分析"
            if model_client and physical_tables:
                modeling_summary = model_client.complete(f"总结业务逻辑: {json.dumps(physical_tables, ensure_ascii=False)}").text.strip()
            unified_schema = {"tables": physical_tables, "macro_context": modeling_summary}
            if semantic_docs and model_client:
                docs = "".join([open(p, 'r', errors='ignore').read()[:5000] for p in semantic_docs])
                try:
                    res = model_client.complete(f"基于物理表 {json.dumps(physical_tables)} 和文档 {docs} 构建全局业务模型。仅返回 JSON 格式。" ).text
                    match = re.search(r'(\{.*\})', res, re.DOTALL)
                    if match:
                        semantic = json.loads(match.group(1))
                        for t, info in semantic.get('tables', {}).items():
                            if t in unified_schema['tables']: unified_schema['tables'][t].update(info)
                            else: unified_schema['tables'][t] = info; unified_schema['tables'][t]['is_virtual'] = True
                        unified_schema['macro_context'] = semantic.get('macro_context', modeling_summary)
                except: pass
            with open(self.schema_path, 'w', encoding='utf-8') as f: json.dump(unified_schema, f, indent=4, ensure_ascii=False)
            if model_client:
                if status_callback: status_callback("🧪 正在执行出厂级数据固化预填充...")
                self._ensure_sandbox_ready(unified_schema, model_client, status_callback=None)
            if status_callback: status_callback(f"✅ 全域建模完成，数据库已持久化就绪")
            return {"success": True, "tables": list(unified_schema['tables'].keys())}
        except Exception as e: return {"success": False, "error": str(e)}