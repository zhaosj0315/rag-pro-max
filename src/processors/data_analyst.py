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
        [v4.5.0 战略版] 宏观语义提取：从文档中识别表结构、业务拓扑及【宏观战略目标】。
        """
        all_text = "\n".join([d.text for d in docs[:30]]) 
        
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
            # [v4.5.6 增强] 强力 JSON 提取逻辑
            import re
            json_match = re.search(r'(\{.*\})', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            schema_data = json.loads(content)
            with open(self.schema_path, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, indent=4, ensure_ascii=False)
            if self.logger: self.logger.success("✨ 业务架构定义已成功存入物理库")
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
        [v5.0 极光战略工作坊] 链式推演引擎：需求拆解 -> 多阶脚本 -> 闭环仿真 -> 综合研判
        """
        if not os.path.exists(self.schema_path):
             return {"success": False, "logic": "未找到数据结构定义，请上传文档或表单。"}

        with open(self.schema_path, 'r', encoding='utf-8') as f:
            full_schemas = json.load(f)
        
        relevant_table_names = self._get_relevant_tables(query, full_schemas)
        pruned_schemas = {
            "macro_context": full_schemas.get("macro_context", "通用业务分析"),
            "tables": {name: full_schemas["tables"][name] for name in relevant_table_names if name in full_schemas["tables"]},
            "relationships": [r for r in full_schemas.get("relationships", []) if r["source"] in relevant_table_names or r["target"] in relevant_table_names]
        }

        # 1. 战略拆解层：将复杂需求拆解为 2-3 个阶段
        decomposition_prompt = f"""
你是一名顶级商业技术顾问。针对用户需求，请将其拆解为 2 个逻辑递进的分析阶段。
需求：{query}
业务模型：{json.dumps(pruned_schemas, ensure_ascii=False)}

请返回标准的 JSON 数组，格式如下：
[
  {{ "stage_id": 1, "title": "阶段标题", "goal": "本阶段要解决的子问题", "logic": "分析逻辑说明" }},
  ...
]
"""
        try:
            decomp_res = model_client.complete(decomposition_prompt).text
            stages_meta = json.loads(decomp_res.strip().replace("```json", "").replace("```", ""))
        except:
            stages_meta = [{"stage_id": 1, "title": "核心逻辑分析", "goal": "执行基础数据摸排", "logic": "直接针对需求进行多表关联分析"}]

        # 2. 链式执行层：为每个阶段生成脚本与数据
        final_stages_data = []
        full_analysis_context = ""

        for meta in stages_meta:
            # A. 针对本阶段生成多方言 SQL
            sql_prompt = f"""针对分析阶段【{meta['title']}】编写多方言 SQL。
子目标：{meta['goal']}
业务背景：{pruned_schemas['macro_context']}
模型：{json.dumps(pruned_schemas['tables'], ensure_ascii=False)}
要求返回 JSON：{{ "sqlite": "...", "dataworks": "...", "standard": "..." }}"""
            
            sqls = {"sqlite": "", "dataworks": "", "standard": ""}
            try:
                sql_res = model_client.complete(sql_prompt).text
                sqls = json.loads(sql_res.strip().replace("```json", "").replace("```", ""))
            except: pass

            # B. 执行与仿真 (制造闭环数据)
            execution_res = {"success": False, "data": []}
            is_simulated = False
            if sqls.get("sqlite"):
                execution_res = self.execute_sql(sqls["sqlite"])
                if not execution_res["success"] or not execution_res["data"]:
                    is_simulated = True
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
            
            # C. 归档本阶段成果
            stage_entry = {
                "meta": meta,
                "sqls": sqls,
                "data": execution_res.get("data", []),
                "is_simulated": is_simulated
            }
            final_stages_data.append(stage_entry)
            full_analysis_context += f"阶段 {meta['stage_id']} ({meta['title']}) 结论数据: {json.dumps(stage_entry['data'][:3], ensure_ascii=False)}\n"

        # 3. 综合研判层：准备最终报告生成器
        summary_prompt = f"""
你是一名首席战略官。请基于以下【多阶段链式推演】结果撰写最终战略报告。
用户原始需求: {query}
业务宏观背景: {pruned_schemas['macro_context']}
各阶段推演数据摘要:
{full_analysis_context}

报告要求：
1. 整合各阶段发现，给出一个贯穿式的宏观结论。
2. 针对每一个阶段的技术实现（SQL）给出工程落地建议。
3. 结合知识库背景，指出未来 3-6 个月的战略预警点。
报告结构包含：### 🗺️ 全局战略地图、### 🔬 阶段性洞察汇编、### 💻 工程落地指南、### 🚀 首席执行建议。
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
            error_str = str(e)
            if "no such table" in error_str.lower():
                if self.logger: self.logger.info("🛠️ 检测到表缺失，尝试从 docstore 紧急恢复...")
                try:
                    self._recover_data_from_docstore()
                    # 恢复后重试一次
                    conn = sqlite3.connect(self.db_path)
                    conn.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
                    cursor = conn.cursor()
                    cursor.execute(sql)
                    rows = cursor.fetchall()
                    conn.close()
                    return {"success": True, "data": rows}
                except Exception as retry_e:
                    if self.logger: self.logger.error(f"SQL 重试失败: {retry_e}")
            
            if self.logger:
                self.logger.error(f"SQL 执行失败: {sql} | Error: {e}")
            return {"success": False, "error": str(e), "data": []}

    def process_files(self, file_paths: List[str]) -> Dict[str, Any]:
        import re
        try:
            if os.path.exists(self.db_path): os.remove(self.db_path)
            conn = sqlite3.connect(self.db_path)
            processed_tables = {}
            has_schema_source = False

            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                # 识别 Markdown 数据字典
                if file_path.lower().endswith(('.md', '.markdown')):
                    has_schema_source = True
                    continue

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
            
            # 如果包含表格文件，生成基础 schema
            if processed_tables:
                with open(self.schema_path, 'w', encoding='utf-8') as f:
                    json.dump({"tables": processed_tables}, f, indent=4, ensure_ascii=False)
            
            return {
                "success": True, 
                "tables": list(processed_tables.keys()), 
                "has_schema_doc": has_schema_source
            }
        except Exception as e:
            if self.logger: self.logger.error(f"文件处理入库失败: {e}")
            return {"success": False, "error": str(e)}
