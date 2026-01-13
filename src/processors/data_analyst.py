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

    def extract_schema_from_docs(self, docs: List[Any], model_client, status_callback=None) -> Dict[str, Any]:
        """
        [v4.5.0 战略版] 宏观语义提取：从文档中识别表结构、业务拓扑及【宏观战略目标】。
        """
        if status_callback: status_callback(f"📄 正在阅读 {len(docs)} 个业务文档...")
        all_text = "\n".join([d.text for d in docs[:30]]) 
        # [Safe Guard] 防止上下文过长导致超时
        if len(all_text) > 60000:
            all_text = all_text[:60000] + "...(truncated)"
            
        if status_callback: status_callback("🧠 正在请求大模型提取业务架构 (可能需要 1-2 分钟)...")
        prompt = f"""
你是一名资深首席架构师与业务战略专家。请从以下文档中提取业务模型与宏观背景。
文档内容：{all_text}

要求输出标准的 JSON，必须包含：
1. "macro_context": "基于文档推断的宏观业务背景、核心 KPI 目标和战略方向"
2. "tables": {{ "表名": {{ "desc": "业务含义", "cols": [{{ "name": "字段名", "type": "类型", "comment": "解释" }}] }} }}
3. "relationships": [ {{ "source": "表A", "target": "表B", "on": "关联字段", "logic": "宏观业务流转逻辑" }} ]
4. "business_domains": {{ "领域名": ["相关表名"] }}

即使文档中仅有数据字典，也请根据字段名推断其在宏观业务中的价值。
"""
        response = model_client.complete(prompt)
        try:
            content = response.text.strip()
            import re
            json_match = re.search(r'(\{.*\})', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            schema_data = json.loads(content)
            with open(self.schema_path, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, indent=4, ensure_ascii=False)
            if self.logger: self.logger.success(f"✨ 业务架构定义已成功存入物理库: {self.schema_path}")
            if status_callback:
                t_names = list(schema_data.get('tables', {}).keys())
                t_preview = ", ".join(t_names)
                status_callback(f"✅ 架构提取完成: 识别到 {len(t_names)} 张业务表 [{t_preview}], 存入 {os.path.basename(self.schema_path)}")
            return schema_data
        except Exception as e:
            if self.logger: self.logger.error(f"战略模型解析失败: {e}")
            return {"error": f"解析失败: {str(e)}"}

    def infer_business_blueprint(self, schemas: Any, model_client) -> Dict[str, Any]:
        """
        [接口恢复] 业务蓝图推演：对接 v3.7.0 架构图谱引擎。
        """
        try:
            if isinstance(schemas, str):
                schemas_str = schemas
            else:
                schemas_str = json.dumps(schemas, indent=2, ensure_ascii=False, default=str)
            
            # [v5.3.1] 防止 Schema 过大导致模型推理超时
            if len(schemas_str) > 8000:
                schemas_str = schemas_str[:8000] + "...(truncated)"
            
            prompt = f"""
请根据以下数据库架构图谱推导业务全景图：
{schemas_str}

请输出标准的 JSON 格式：
{{
  "business_scenario": "业务系统描述",
  "core_logic": "核心业务流转逻辑",
  "analysis_dimensions": ["维度1", "维度2", "维度3", "维度4", "维度5"]
}}
"""
            response = model_client.complete(prompt)
            content = response.text.strip()
            # 增强型 JSON 提取
            import re
            json_match = re.search(r'(\{.*\})', content, re.DOTALL)
            if json_match: content = json_match.group(1)
            
            blueprint = json.loads(content)
            with open(self.blueprint_path, 'w', encoding='utf-8') as f:
                json.dump(blueprint, f, indent=4, ensure_ascii=False)
            return blueprint
        except Exception as e:
            if self.logger: self.logger.error(f"业务蓝图推演失败: {e}")
            return {
                "business_scenario": "基于当前架构推演业务全景",
                "core_logic": "多维业务数据分析与战略决策支持",
                "analysis_dimensions": ["业务趋势分析", "风险预警", "资源优化", "绩效评估", "战略对齐"],
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

    def _ensure_sandbox_ready(self, schemas: Dict[str, Any], model_client, status_callback=None):
        """
        [v5.3.1] 虚拟沙盒激活：增加 dual 表支持与仿真数据注入。
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # A. 创建 DUAL 表垫片 (解决 no such table: dual)
        cursor.execute("CREATE TABLE IF NOT EXISTS dual (dummy TEXT)")
        cursor.execute("SELECT count(*) FROM dual")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO dual (dummy) VALUES ('X')")
        
        tables_to_mock = []
        tables_ready = []
        for t_name, info in schemas.get('tables', {}).items():
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{t_name}'")
            if not cursor.fetchone():
                tables_to_mock.append(t_name)
            else:
                tables_ready.append(t_name)
        
        if tables_ready and status_callback:
            status_callback(f"✅ 已就绪业务表: {', '.join(tables_ready[:5])}...")

        if tables_to_mock and model_client:
            if self.logger: self.logger.info(f"🚧 正在为虚拟表 {tables_to_mock} 制造仿真数据...")
            if status_callback: status_callback(f"🚧 检测到 {len(tables_to_mock)} 张表暂无本地数据，正在启动仿真引擎...")
            
            for idx, t_name in enumerate(tables_to_mock):
                if status_callback: status_callback(f"🎲 [{idx+1}/{len(tables_to_mock)}] 正在为 '{t_name}' 生成高保真仿真数据...")
                t_info = schemas['tables'][t_name]
                cols_str = ", ".join([f"{c['name']} (注释: {c.get('comment', '无')})" for c in t_info.get('cols', t_info.get('columns', []))])
                
                mock_prompt = f"""
请为以下业务表生成 20 条【逻辑闭环】的仿真数据。
表名：{t_name}
字段定义：{cols_str}
业务背景：{schemas.get('macro_context', '通用业务')}

要求：
1. 输出标准的 SQL INSERT 语句（适配 SQLite）。
2. **严格的字符串转义**：字符串值必须用单引号包裹（如 'Value'）。如果内容包含单引号，必须使用双单引号转义（例如：'Men''s T-Shirt'）。
3. **严禁使用双引号**包裹字符串值（双引号仅用于列名）。
4. 仅输出 SQL 语句，不要解释。
"""
                try:
                    mock_sql = model_client.complete(mock_prompt).text
                    # 清理并执行 SQL
                    for sql_line in mock_sql.split(';'):
                        clean_sql = sql_line.strip()
                        if clean_sql.upper().startswith(('CREATE', 'INSERT')):
                            if clean_sql.upper().startswith('INSERT') and "CREATE" not in mock_sql:
                                cols_def = ", ".join([f"{c['name']} TEXT" for c in t_info.get('cols', t_info.get('columns', []))])
                                cursor.execute(f"CREATE TABLE IF NOT EXISTS {t_name} ({cols_def})")
                            
                            try:
                                cursor.execute(clean_sql)
                            except Exception as sql_err:
                                # [v5.6.1] 自动修复机制：针对 'Men's T-Shirt' 等未转义问题
                                if "syntax error" in str(sql_err) or "no such column" in str(sql_err):
                                    if self.logger: self.logger.warning(f"⚠️ SQL执行失败，尝试自动修复: {clean_sql[:50]}...")
                                    fix_prompt = f"Fix SQLite error: {str(sql_err)}\nBad SQL: {clean_sql}\nOutput ONLY the fixed SQL statement without markdown."
                                    try:
                                        fixed_sql = model_client.complete(fix_prompt).text.strip().replace("```sql", "").replace("```", "")
                                        cursor.execute(fixed_sql)
                                        if self.logger: self.logger.success(f"🔧 自动修复成功")
                                    except:
                                        raise sql_err
                                else:
                                    raise sql_err
                except Exception as e:
                    if self.logger: self.logger.error(f"仿真数据注入失败 ({t_name}): {e}")
        
        conn.commit()
        conn.close()

    def execute_analysis(self, query: str, model_client, context_text: str = "", status_callback=None) -> Dict[str, Any]:
        """
        [v5.0 极光战略工作坊] 链式推演引擎：需求拆解 -> 多阶脚本 -> 闭环仿真 -> 综合研判
        """
        if status_callback: status_callback("🧠 正在初始化业务语义环境...")
        if not os.path.exists(self.schema_path):
             return {"success": False, "logic": "未找到数据结构定义，请上传文档或表单。"}

        with open(self.schema_path, 'r', encoding='utf-8') as f:
            full_schemas = json.load(f)
        
        self._ensure_sandbox_ready(full_schemas, model_client, status_callback=status_callback)
        relevant_table_names = self._get_relevant_tables(query, full_schemas)
        pruned_schemas = {
            "macro_context": full_schemas.get("macro_context", "通用业务分析"),
            "tables": {name: full_schemas["tables"][name] for name in relevant_table_names if name in full_schemas["tables"]},
            "relationships": [r for r in full_schemas.get("relationships", []) if r["source"] in relevant_table_names or r["target"] in relevant_table_names]
        }

        if status_callback: status_callback("🎯 正在拆解战略目标与分析路径...")
        decomposition_prompt = f"""
你是一名顶级商业技术顾问。针对用户需求，请将其拆解为 2 个逻辑递进的分析阶段。
需求：{query}
业务模型：{json.dumps(pruned_schemas, ensure_ascii=False)}

请返回标准的 JSON 数组，格式如下：
[
  {{
    "stage_id": 1, 
    "title": "阶段标题", 
    "requirement": "【需求理解】本阶段要解决的业务核心痛点是什么",
    "transformation": "【技术转化】本阶段将如何通过数据加工（逻辑、表、指标）来满足上述需求",
    "goal": "具体执行目标", 
    "logic": "核心算法说明" 
  }},
  ...
]"""
        try:
            decomp_res = model_client.complete(decomposition_prompt).text
            stages_meta = json.loads(decomp_res.strip().replace("```json", "").replace("```", ""))
            if status_callback: status_callback(f"✅ 拆解完成: 已规划 {len(stages_meta)} 个核心分析阶段")
        except:
            stages_meta = [{"stage_id": 1, "title": "核心逻辑分析", "goal": "执行基础数据摸排", "logic": "直接针对需求进行多表关联分析"}]
            if status_callback: status_callback("⚠️ 拆解异常，降级为单阶段通用分析")

        final_stages_data = []
        full_analysis_context = ""

        for i, meta in enumerate(stages_meta):
            if status_callback: status_callback(f"⚙️ [Stage {meta['stage_id']}/{len(stages_meta)}] 正在构建: {meta['title']} (生成SQL中...)")
            analysis_path = meta.get('transformation', meta.get('title', '业务逻辑推演'))
            # [v5.2.6] SQL 生成指令优化：调整输出顺序优先级 (DataWorks > Standard > SQLite)
            sql_prompt = f"""
基于分析路径："{analysis_path}"，请编写高度可读、带有详细业务注释的多方言 SQL。
业务背景：{pruned_schemas['macro_context']}
模型：{json.dumps(pruned_schemas['tables'], ensure_ascii=False)}

要求：
1. **必须包含详细注释**：使用 '--' 对每一段逻辑进行说明。
2. **注释内容**：
   - 标注使用的原始表业务含义。
   - 标注关键字段或计算公式的业务逻辑。
   - 标注 JOIN 关联的血缘依据。
3. 返回一个 JSON 对象，包含三个字段（注意顺序）：
   - "dataworks": "生产环境 SQL (MaxCompute语法)，必须包含 ${{bizdate}} 变量"
   - "standard": "标准 ANSI SQL (用于通用数据库验证)"
   - "sqlite": "本地验证 SQL (用于当前环境执行)"

仅返回 JSON，不要有其他解释。"""
            
            sqls = {"dataworks": "", "standard": "", "sqlite": ""}
            try:
                sql_res = model_client.complete(sql_prompt).text
                sqls = json.loads(sql_res.strip().replace("```json", "").replace("```", ""))
                if status_callback: status_callback(f"✅ SQL生成完毕 (覆盖 {len(sqls)} 种方言)")
            except: 
                if status_callback: status_callback("⚠️ SQL生成异常，将使用空模板")

            if status_callback: status_callback(f"🧪 [Stage {meta['stage_id']}] 正在执行逻辑验证...")
            execution_res = {"success": False, "data": []}
            is_simulated = False
            source_samples = {}
            
            for t_name in relevant_table_names:
                s_res = self.execute_sql(f"SELECT * FROM {t_name} LIMIT 3")
                if s_res["success"] and s_res["data"]:
                    source_samples[t_name] = s_res["data"]
                else:
                    source_samples[t_name] = [{"info": f"正在基于 {t_name} 模型进行逻辑模拟..."}]

            if sqls.get("sqlite"):
                execution_res = self.execute_sql(sqls["sqlite"])
                if not execution_res["success"] or not execution_res["data"]:
                    is_simulated = True
                    if status_callback: status_callback(f"🎲 [Stage {meta['stage_id']}] 本地数据不足，启动战略仿真模式 (生成虚拟趋势数据)...")
                    sim_prompt = f"""【战略仿真模式】为阶段：{meta['title']} 制造 10 条反映宏观趋势的“黄金模拟数据”。
业务背景：{pruned_schemas['macro_context']}
逻辑依赖：{meta['logic']}
表结构：{json.dumps(pruned_schemas['tables'], ensure_ascii=False)}

要求：
1. 数据必须逻辑闭环（如：金额必须符合业务常识，日期要有连续性）。
2. **宏观特征**：模拟出的数据应包含 1-2 处“异常点”或“显著趋势”，以供战略分析使用。
3. 仅返回 JSON 数组格式。"""
                    try:
                        sim_out = model_client.complete(sim_prompt).text
                        import re
                        json_match = re.search(r'(\[.*\])', sim_out, re.DOTALL)
                        if json_match: execution_res = {"success": True, "data": json.loads(json_match.group(1))}
                    except: pass
            
            stage_entry = {
                "meta": meta,
                "sqls": sqls,
                "data": execution_res.get("data", []),
                "source_samples": source_samples,
                "is_simulated": is_simulated
            }
            final_stages_data.append(stage_entry)
            rows_count = len(stage_entry['data'])
            if status_callback: status_callback(f"📊 [Stage {meta['stage_id']}] 阶段完成: 产出 {rows_count} 条结论数据")
            full_analysis_context += f"阶段 {meta['stage_id']} ({meta['title']}) 结论数据: {json.dumps(stage_entry['data'][:3], ensure_ascii=False)}\n"

        if status_callback: status_callback("📝 正在撰写首席执行官战略报告...")
        summary_prompt = f"""
你是一名首席战略官。请基于以下【多阶段链式推演】的实际结果撰写最终战略报告。
用户原始需求: {query}
业务宏观背景: {pruned_schemas['macro_context']}
各阶段推演数据摘要:
{full_analysis_context}

要求（严格执行）：
1. **真实性第一**：报告中的每一个百分比、每一个地区名称必须与“推演数据摘要”中提供的 JSON 内容完全一致。
2. **严禁编造**：如果数据摘要中只有 East/West，严禁在报告中提到北美、欧洲等虚假信息。
3. 如果数据是仿真的，请在开头明确标注：“当前分析基于业务架构模型仿真得出”。
4. 报告结构包含：### 🗺️ 全局战略地图、### 🔬 阶段性洞察汇编、### 💻 工程落地指南、### 🚀 首席执行建议。
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
                except: yield "战略推演报告生成异常"
            else:
                res = model_client.complete(summary_prompt).text
                for char in res: yield char

        return {
            "stages": final_stages_data,
            "logic_gen": report_generator(),
            "success": True,
            "macro_context": pruned_schemas['macro_context']
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
            error_str = str(e)
            if "no such table" in error_str.lower():
                try:
                    self._recover_data_from_docstore()
                    conn = sqlite3.connect(self.db_path)
                    conn.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
                    cursor = conn.cursor()
                    cursor.execute(sql)
                    rows = cursor.fetchall()
                    conn.close()
                    return {"success": True, "data": rows}
                except: pass
            return {"success": False, "error": str(e), "data": []}

    def process_files(self, file_paths: List[str], model_client=None, status_callback=None) -> Dict[str, Any]:
        """
        [v5.3 战略版] 全域开模引擎：支持全格式输入 (PDF/MD/CSV/XLSX) 统一建模。
        """
        import re
        try:
            if os.path.exists(self.db_path): os.remove(self.db_path)
            conn = sqlite3.connect(self.db_path)
            
            physical_tables = {}
            semantic_docs = []
            
            if status_callback: status_callback(f"📊 正在处理 {len(file_paths)} 个源文件...")
            
            for file_path in file_paths:
                file_name = os.path.basename(file_path).lower()
                if file_name.endswith(('.md', '.markdown', '.pdf', '.docx', '.txt')):
                    semantic_docs.append(file_path)
                    continue

                table_name = os.path.splitext(file_name)[0]
                table_name = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5]', '_', table_name)
                
                try:
                    if file_name.endswith('.csv'): df = pd.read_csv(file_path)
                    elif file_name.endswith(('.xls', '.xlsx')): df = pd.read_excel(file_path)
                    else: continue
                    
                    df.columns = [re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5]', '_', str(c)) for c in df.columns]
                    df.to_sql(table_name, conn, index=False, if_exists='replace')
                    
                    physical_tables[table_name] = {
                        "source": file_name,
                        "columns": [{"name": c, "type": str(t)} for c, t in df.dtypes.items()]
                    }
                except Exception as e:
                    if self.logger: self.logger.warning(f"物理表 {file_name} 解析跳过: {e}")
            
            conn.close()

            unified_schema = {"tables": physical_tables, "macro_context": "通用业务分析", "relationships": []}
            
            if semantic_docs and model_client:
                if self.logger: self.logger.info(f"🧠 正在从 {len(semantic_docs)} 个源材料中提取战略模型...")
                if status_callback: status_callback(f"🧠 正在从 {len(semantic_docs)} 个源材料中提取战略模型...")
                docs_content = []
                for doc_path in semantic_docs:
                    with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                        docs_content.append(f.read()[:5000])
                
                prompt = f"""
你是一名资深架构师。请结合以下【物理表结构】与【业务材料内容】，构建统一的业务模型。
【物理表结构】：{json.dumps(physical_tables, ensure_ascii=False)}
【业务材料】：{"".join(docs_content)}

要求输出标准 JSON：
1. "macro_context": "基于文档推断的宏观背景与 KPI 定义"
2. "tables": {{ 
      "表名": {{ 
         "desc": "业务含义", 
         "is_virtual": true/false(物理表为false),
         "cols": [{{ "name": "字段名", "comment": "从文档中识别的业务定义" }}] 
      }} 
   }}
3. "relationships": [ {{ "source": "表A", "target": "表B", "on": "关联字段", "logic": "业务流转逻辑" }} ]
"""
                res = model_client.complete(prompt).text
                try:
                    json_match = re.search(r'(\{.*\})', res, re.DOTALL)
                    if json_match:
                        semantic_schema = json.loads(json_match.group(1))
                        for t_name, t_info in semantic_schema.get('tables', {}).items():
                            if t_name in unified_schema['tables']:
                                unified_schema['tables'][t_name].update(t_info)
                                unified_schema['tables'][t_name]['is_virtual'] = False
                            else:
                                unified_schema['tables'][t_name] = t_info
                                unified_schema['tables'][t_name]['is_virtual'] = True
                        
                        unified_schema['macro_context'] = semantic_schema.get('macro_context', unified_schema['macro_context'])
                        unified_schema['relationships'] = semantic_schema.get('relationships', [])
                except: pass

            with open(self.schema_path, 'w', encoding='utf-8') as f:
                json.dump(unified_schema, f, indent=4, ensure_ascii=False)
            
            if status_callback:
                t_names = list(unified_schema['tables'].keys())
                t_preview = ", ".join(t_names)
                status_callback(f"✅ 全域建模完成: 包含 {len(t_names)} 张表 [{t_preview}], 定义已存入 {os.path.basename(self.schema_path)}")
            
            return {
                "success": True, 
                "tables": list(unified_schema['tables'].keys()),
                "has_virtual": any(t.get('is_virtual') for t in unified_schema['tables'].values())
            }
        except Exception as e:
            if self.logger: self.logger.error(f"全域开模失败: {e}")
            return {"success": False, "error": str(e)}