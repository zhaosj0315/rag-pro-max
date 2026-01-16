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
        if len(all_tables) <= 5: return list(all_tables.keys())
        relevant = []
        qw = query.lower()
        for t, info in all_tables.items():
            if t.lower() in qw or any(w in str(info.get("desc","")).lower() for w in qw if len(w)>1):
                relevant.append(t)
        return list(set(relevant))[:8]

    def _ensure_sandbox_ready(self, schemas: Dict[str, Any], model_client, status_callback=None, target_tables: List[str] = None) -> Dict[str, str]:
        """[v6.7.0] 数据库就绪检查：强制物理优先，严禁对已存物理表进行仿真"""
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
                table_mapping[t] = match
                continue
            tables_to_mock.append(t)

        if tables_to_mock and model_client:
            if status_callback: status_callback(f"🎲 正在为 {len(tables_to_mock)} 个扩展实体生成仿真数据...")
            for t in tables_to_mock:
                info = schemas['tables'].get(t, {})
                cols = info.get('cols', info.get('columns', []))
                cols_str = ", ".join([f"{c['name']} ({c.get('comment','')})" for c in cols])
                prompt = f"为表 {t} 生成 20 条 INSERT SQL。\n字段：{cols_str}\n仅输出 SQL 代码。"
                try:
                    res = model_client.complete(prompt).text
                    cursor.execute(f"CREATE TABLE IF NOT EXISTS {t} ({', '.join([f'{c['name']} TEXT' for c in cols])})")
                    for line in res.split(';'):
                        if 'INSERT' in line.upper(): cursor.execute(line.strip())
                except: pass
        conn.commit()
        conn.close()
        return table_mapping

    def execute_analysis(self, query: str, model_client, context_text: str = "", status_callback=None) -> Dict[str, Any]:
        if not os.path.exists(self.schema_path): return {"success": False, "logic": "架构缺失"}
        with open(self.schema_path, 'r', encoding='utf-8') as f: full_schemas = json.load(f)
        
        # 1. 元数据直查
        if any(k in query for k in ["指标", "结构", "字典", "有哪些表"]):
            prompt = f"基于以下模型回答问题: {query}\n{json.dumps(full_schemas, ensure_ascii=False)[:4000]}"
            def gen():
                for char in model_client.complete(prompt).text: yield char
            return {"stages":[], "logic_gen": gen(), "success":True, "macro_context":"架构咨询"}

        # 2. 识别与对齐
        rel_tables = self._get_relevant_tables(query, full_schemas)
        mapping = self._ensure_sandbox_ready(full_schemas, model_client, status_callback, rel_tables)
        
        # 3. 构建精简 Schema
        pruned_tables = {}
        for t in rel_tables:
            real_t = mapping.get(t, t)
            info = full_schemas['tables'].get(t, {})
            cols = info.get('cols', info.get('columns', []))
            # 语义保留：强制保留状态、日期和金额字段
            keep = ['status', 'state', 'date', 'time', 'amount', 'price', 'total', 'id', 'name', '状态', '日期', '金额']
            filtered = [c for c in cols if any(k in c['name'].lower() or k in str(c.get('comment','')).lower() for k in keep)]
            pruned_tables[real_t] = {"desc": info.get("desc"), "cols": filtered if filtered else cols[:10]}

        # 4. 任务拆解
        prompt = f"将需求 {query} 拆解为 2-3 个 SQL 分析阶段。返回 JSON 数组: [{{stage_id, title, transformation, goal}}]\n模型: {json.dumps(pruned_tables, ensure_ascii=False)}"
        try:
            res = model_client.complete(prompt).text
            stages_meta = json.loads(re.search(r'(\[.*\])', res, re.DOTALL).group(1))
        except: stages_meta = [{"stage_id": 1, "title": "数据透视", "transformation": "全量聚合分析"}]

        final_data = []
        context = ""
        for i, meta in enumerate(stages_meta):
            if status_callback: status_callback(f"⚙️ [Stage {i+1}] 生成 SQL 指令...")
            
            # 样本探测
            samples = ""
            for t in pruned_tables:
                r = self.execute_sql(f"SELECT * FROM {t} LIMIT 1")
                if r["success"] and r["data"]:
                    samples += f"表 {t} 样例: {json.dumps(r['data'][0], ensure_ascii=False)}\n"

            sql_prompt = f"编写 SQLite SQL。路径: {meta.get('transformation')}\n背景: {full_schemas.get('macro_context')}\n模型: {json.dumps(pruned_tables, ensure_ascii=False)}\n样例: {samples}\n前序结论: {context}\n【严格输出 JSON】: {{"sqlite": "SELECT...", "standard": "...", "dataworks": "..."}}"
sqls = {"sqlite": ""}
try:
                res = model_client.complete(sql_prompt).text
                m = re.search(r'(\{.*\})', res, re.DOTALL)
                if m: sqls = json.loads(m.group(1).replace('\\n',' '))
            except: pass

            if status_callback: status_callback(f"🧪 [Stage {i+1}] 执行并验证...")
            exec_res = {"success": False, "data": []}
            if sqls.get("sqlite"):
                exec_res = self.execute_sql(sqls["sqlite"], model_client)
                if exec_res["success"] and exec_res["data"]:
                    if status_callback: status_callback(f"✅ 获取 {len(exec_res['data'])} 行数据")
                    context += f"阶段{i+1}: {json.dumps(exec_res['data'][:1], ensure_ascii=False)}\n"
            
            final_data.append({"meta": meta, "sqls": sqls, "data": exec_res["data"]})

        # 5. 撰写报告
        def report_gen():
            p = f"撰写战略报告。需求: {query}\n结果摘要: {context}\n要求: SCQA 架构，结论先行。"
            if hasattr(model_client, 'stream_chat'):
                from llama_index.core.base.llms.types import ChatMessage, MessageRole
                try:
                    for chunk in model_client.stream_chat([ChatMessage(role=MessageRole.USER, content=p)]):
                        yield chunk.delta if hasattr(chunk, 'delta') else str(chunk)
                except: yield "生成中断"
            else: yield model_client.complete(p).text

        return {"stages": final_data, "logic_gen": report_gen(), "success": True, "macro_context": full_schemas.get('macro_context','')}

    def execute_sql(self, sql: str, model_client=None) -> Dict[str, Any]:
        try:
            conn = sqlite3.connect(self.db_path, timeout=30)
            conn.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
            cursor = conn.cursor()
            clean_sql = sql.replace('\\
', ' ').replace('\\', '')
            statements = [s.strip() for s in clean_sql.split(';') if s.strip()]
            rows = []
            for stmt in statements:
                if not stmt: continue
                try:
                    cursor.execute(stmt)
                    if stmt.upper().startswith("SELECT"): rows = cursor.fetchall()
                except Exception as e:
                    if model_client and stmt.upper().startswith("SELECT"):
                        fix = model_client.complete(f"修复 SQL 语法错误: {e}\n错误 SQL: {stmt}\n仅输出修正后的一条 SQL").text
                        cursor.execute(re.sub(r'```sql|```', '', fix, flags=re.I).strip())
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
            if status_callback: status_callback(f"📊 正在解析 {len(file_paths)} 个源材料...")
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
                    if status_callback: status_callback(f"✅ 表 '{t_name}' 物理导入成功 ({count} 行数据)")
                    physical_tables[t_name] = {"cols": [{"name": c, "type": str(t)} for c, t in df.dtypes.items()]}
                except: pass
            conn.close()
            modeling_summary = "业务数据分析"
            if model_client and physical_tables:
                modeling_summary = model_client.complete(f"总结业务逻辑: {json.dumps(physical_tables, ensure_ascii=False)}").text.strip()
            unified_schema = {"tables": physical_tables, "macro_context": modeling_summary}
            if semantic_docs and model_client:
                docs = "".join([open(p, 'r', errors='ignore').read()[:5000] for p in semantic_docs])
                try:
                    res = model_client.complete(f"结合物理表 {json.dumps(physical_tables)} 和文档 {docs} 构建模型。返回 JSON").text
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
                if status_callback: status_callback("🧪 正在执行出厂级高保真数据预填充...")
                self._ensure_sandbox_ready(unified_schema, model_client, status_callback=None)
            if status_callback: status_callback(f"✅ 建模完成，数据库已固化")
            return {"success": True, "tables": list(unified_schema['tables'].keys())}
        except Exception as e: return {"success": False, "error": str(e)}