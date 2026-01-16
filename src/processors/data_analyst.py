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
        """[v6.6.0] 加载分析记忆库"""
        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return []

    def _save_memory(self, query: str, sql: str, goal: str):
        """[v6.6.0] 沉淀分析经验"""
        try:
            memories = self._load_memory()
            for m in memories:
                if m['query'] == query: return
            
            memories.append({
                "query": query,
                "goal": goal,
                "sql": sql,
                "timestamp": datetime.now().isoformat()
            })
            if len(memories) > 50: memories = memories[-50:]
            
            with open(self.memory_path, 'w', encoding='utf-8') as f:
                json.dump(memories, f, indent=2, ensure_ascii=False)
        except: pass

    def extract_schema_from_docs(self, docs: List[Any], model_client, status_callback=None) -> Dict[str, Any]:
        """
        [v4.5.0 战略版] 宏观语义提取：从文档中识别表结构、业务拓扑及【宏观战略目标】。
        """
        if status_callback: status_callback(f"📄 正在阅读 {len(docs)} 个业务文档...")
        all_text = "\n".join([d.text for d in docs[:30]]) 
        if len(all_text) > 60000:
            all_text = all_text[:60000] + "...(truncated)"
            
        if status_callback: status_callback("🧠 正在请求大模型提取业务架构 (可能需要 1-2 分钟)...")
        
        prompt = f"""
你是一名资深首席架构师。请从以下文档中【严谨提取】业务模型与宏观背景。

【重要约束】:
1. **严禁凭空想象**：不要生成文档中未提及的表结构。代理表生成
2. **物理表对齐**：如果文档中包含物理表字段定义，请以物理表名为准。
3. **识别业务领域**：基于文档真实内容推断 KPI 目标。

文档内容：
{all_text}

要求输出标准的 JSON，必须包含：
1. "macro_context": "基于文档内容的业务背景与战略方向"
2. "tables": {{ "表名": {{ "desc": "业务含义", "cols": [{{ "name": "字段名", "type": "类型", "comment": "解释" }}] }} }}
3. "relationships": [ {{ "source": "表A", "target": "表B", "on": "关联字段", "logic": "业务流转逻辑" }} ]
4. "business_domains": {{ "领域名": ["相关表名"] }}
"""
        response = model_client.complete(prompt)
        try:
            content = response.text.strip()
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

    def _ensure_sandbox_ready(self, schemas: Dict[str, Any], model_client, status_callback=None, target_tables: List[str] = None) -> Dict[str, str]:
        """
        [v6.6.2] 虚拟沙盒加固：增加表名模糊映射与自愈能力。
        [v6.6.4] 按需加载：支持仅检查 target_tables 指定的表。
        返回: table_mapping (虚拟名 -> 物理名)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # A. 创建 DUAL 表垫片
        cursor.execute("CREATE TABLE IF NOT EXISTS dual (dummy TEXT)")
        cursor.execute("SELECT count(*) FROM dual")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO dual (dummy) VALUES ('X')")
        
        tables_to_mock = []
        tables_ready = []
        table_mapping = {} # new: 记录 schema表名 -> 真实物理表名 的映射
        
        # 获取真实的物理表清单 (保留原始大小写以便映射)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        physical_tables_raw = [row[0] for row in cursor.fetchall()]
        physical_tables_lower = {t.lower(): t for t in physical_tables_raw} # lower -> original
        
        # [v6.6.3] 调试公示
        if self.logger: 
            self.logger.info(f"📂 [Debug] 物理库现有表清单: {physical_tables_raw}")
        if status_callback and len(physical_tables_raw) > 0 and not target_tables:
            display_tables = [t for t in physical_tables_raw if t.lower() not in ('dual', 'sqlite_sequence')]
            if display_tables:
                status_callback(f"📂 物理库实存表 ({len(display_tables)}张): {', '.join(display_tables[:5])}..." )

        # [Helper] 模糊匹配逻辑
        def find_physical_match(target_name):
            target = target_name.lower()
            if target in physical_tables_lower: return physical_tables_lower[target]
            if target + 's' in physical_tables_lower: return physical_tables_lower[target + 's']
            if target.endswith('s') and target[:-1] in physical_tables_lower: return physical_tables_lower[target[:-1]]
            
            candidates = [f"{target}_list", f"{target}_info", f"{target}_data", f"t_{target}", f"tbl_{target}", f"raw_{target}"]
            for cand in candidates:
                if cand in physical_tables_lower: return physical_tables_lower[cand]
            
            for real_t in physical_tables_lower:
                if real_t.endswith(f"_{target}") or real_t.startswith(f"{target}_"): return physical_tables_lower[real_t]
            return None

        # 确定要检查的表范围
        tables_to_check = target_tables if target_tables else list(schemas.get('tables', {}).keys())

        for t_name in tables_to_check:
            # 确保 t_name 在 schemas 中存在
            if t_name not in schemas.get('tables', {}): continue

            t_name_str = str(t_name)
            if "." in t_name_str or t_name_str.lower().startswith("sqlite_") or t_name_str.lower() == "dual": continue

            physical_match = find_physical_match(t_name_str)
            
            if physical_match:
                # [v6.6.5] 数据持久化校验：表存在不代表有数据
                try:
                    row_count = cursor.execute(f"SELECT count(*) FROM {physical_match}").fetchone()[0]
                except: row_count = 0

                if row_count > 0:
                    # 表存在且有数据 -> 完美复用
                    if physical_match != t_name_str:
                        table_mapping[t_name_str] = physical_match
                    tables_ready.append(physical_match)
                    if self.logger: self.logger.info(f"💾 复用现有数据: {physical_match} ({row_count} 行)")
                else:
                    # 表存在但为空 -> 需要补全数据
                    tables_to_mock.append(t_name_str)
            else:
                # 表不存在 -> 需要建表并仿真
                tables_to_mock.append(t_name_str)
        
        if tables_to_mock and model_client:
            final_mock_list = []
            for t in tables_to_mock:
                is_pure_virtual = schemas['tables'].get(t, {}).get('is_virtual', False)
                if is_pure_virtual: final_mock_list.append(t)
                else:
                    final_mock_list.append(t)
            
            if final_mock_list:
                if status_callback: status_callback(f"🎲 [按需加载] 正在为 {len(final_mock_list)} 个相关缺失实体生成仿真数据...")
                
                for idx, t_name in enumerate(final_mock_list):
                    t_info = schemas['tables'].get(t_name, {})
                    cols = t_info.get('cols', t_info.get('columns', []))
                    cols_str = ", ".join([f"{c['name']} (注释: {c.get('comment', '无')})" for c in cols])
                    
                    mock_prompt = f"请为以下业务表生成 20 条【逻辑闭环】的仿真数据。\n表名：{t_name}\n字段定义：{cols_str}\n要求：SQLite INSERT语句，单引号转义，仅输出SQL。"
                    try:
                        mock_sql = model_client.complete(mock_prompt).text
                        cols_def = ", ".join([f"{c['name']} TEXT" for c in cols])
                        cursor.execute(f"CREATE TABLE IF NOT EXISTS {t_name} ({cols_def})")
                        for sql_line in mock_sql.split(';'):
                            clean_sql = sql_line.strip()
                            if clean_sql.upper().startswith('INSERT'):
                                cursor.execute(clean_sql)
                    except Exception: pass
        
        conn.commit()
        conn.close()
        return table_mapping

    def recommend_visualization(self, query: str, columns: List[str], sample_data: List[Dict], model_client) -> Dict[str, Any]:
        """
        [v5.8.0] 智能可视化推荐引擎：根据查询意图和数据特征推荐最佳图表。
        """
        prompt = f"""
你是一名资深数据可视化专家。请根据用户查询和返回的数据样本，推荐最适合的可视化图表类型。

用户查询: {query}
数据列: {columns}
数据样本 (前3行): {json.dumps(sample_data[:3], ensure_ascii=False, default=str)}

        请深入分析数据特征（类别型、数值型、时间序列）和查询意图（对比、分布、趋势、占比、转化、流转），从以下类型中选择一种最能洞察数据的图表: 
["bar", "line", "pie", "scatter", "area", "box", "histogram", "heatmap", "funnel", "treemap", "sunburst", "radar", "indicator", "table"]

- **bar (柱状图)**: 适合比较不同类别的数值大小。
- **line (折线图)**: 适合展示连续时间序列的趋势变化。
- **pie (饼图)**: 适合展示部分占整体的比例。
- **funnel (漏斗图)**: **[业务推荐]** 适合展示业务流程的转化率（如：营销转化、订单全链路监控）。
- **treemap (矩形树图)**: **[业务推荐]** 适合展示具有层级关系的大量数据分布（如：品类->品牌->单品的销售分布）。
- **sunburst (旭日图)**: 适合展示多层级占比，比饼图更具深度。
- **radar (雷达图)**: **[业务推荐]** 适合对比多个对象的多个维度属性（如：不同供应商的质量、价格、交期对比）。
- **indicator (KPI 指标卡)**: **[核心监控]** 适合展示单一核心指标的数值及其变化率。
- **scatter/box/histogram/heatmap**: 用于专业的数据分布与相关性分析。
- **table (表格)**: 仅当数据无法有效可视化时使用。

请返回标准 JSON 格式:
{{
  "viz_type": "推荐的图表类型",
  "x_axis": "X轴字段名 (主要分类维度)",
  "y_axis": "Y轴字段名 (主要数值指标)",
  "color": "分组/颜色字段名 (可选)",
  "path": ["层级1", "层级2"], (仅用于 treemap/sunburst),
  "title": "图表标题",
  "insight": "中英双语图表业务结论 (格式: '中文发现 | English Insight', 概括数据中的核心业务发现)",
  "reason": "推荐理由 (请从业务价值角度说明为什么选择此图表)"
}}
"""
        try:
            response = model_client.complete(prompt).text
            import re
            json_match = re.search(r'(\{.*\})', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            return {"viz_type": "table", "reason": "无法解析推荐结果"}
        except Exception as e:
            if self.logger: self.logger.warning(f"可视化推荐失败: {e}")
            return {"viz_type": "table", "reason": str(e)}

    def execute_analysis(self, query: str, model_client, context_text: str = "", status_callback=None) -> Dict[str, Any]:
        """
        [v6.6.8] 极光战略工作坊：增加元数据感知与按需加载保护。
        """
        if status_callback: status_callback("🧠 正在初始化业务语义环境...")
        if not os.path.exists(self.schema_path):
             return {"success": False, "logic": "未找到数据结构定义，请上传文档或表单。"}

        with open(self.schema_path, 'r', encoding='utf-8') as f:
            full_schemas = json.load(f)
        
        # --- [v6.6.8] 策略 A: 元数据意图拦截 ---
        metadata_keywords = ["有哪些指标", "关键数据指标", "指标说明", "数据字典", "表结构", "有哪些表", "数据模型"]
        if any(k in query for k in metadata_keywords):
            if status_callback: status_callback("📖 检测到元数据查询意图，正在从业务架构定义中提取答案...")
            schema_summary = []
            for t_name, t_info in full_schemas.get('tables', {}).items():
                cols = [f"{c['name']}({c.get('comment','无')})" for c in t_info.get('cols', t_info.get('columns', []))[:10]]
                schema_summary.append(f"- 表: {t_name} ({t_info.get('desc', '业务实体')})\n  字段: {', '.join(cols)}")
            summary_prompt = f"请根据以下业务模型定义，详细解答用户的疑问：{query}\n\n模型定义：\n" + "\n".join(schema_summary)
            def metadata_gen():
                res = model_client.complete(summary_prompt).text
                for char in res: yield char
            return {"stages": [], "logic_gen": metadata_gen(), "success": True, "macro_context": full_schemas.get('macro_context', "业务架构咨询")}

        # --- [v6.6.8] 策略 B: 正常数据分析流 ---
        # 1. 先识别相关表
        relevant_table_names = self._get_relevant_tables(query, full_schemas)
        if len(relevant_table_names) > 10:
            if status_callback: status_callback(f"⚠️ 检测到问题涉及范围过广 ({len(relevant_table_names)}张表)，已自动剪枝以保护计算资源。")
            relevant_table_names = relevant_table_names[:10]
        
        # 2. 仅对相关表进行检查和仿真
        table_mapping = self._ensure_sandbox_ready(full_schemas, model_client, status_callback=status_callback, target_tables=relevant_table_names)
        
        # 3. 应用映射并构建 pruned_schemas
        mapped_relevant_tables = []
        corrected_schemas = {"tables": {}, "relationships": [], "macro_context": full_schemas.get("macro_context", "")}
        
        for t_name, t_info in full_schemas.get("tables", {}).items():
            real_name = table_mapping.get(t_name, t_name)
            corrected_schemas["tables"][real_name] = t_info
            if t_name in relevant_table_names:
                mapped_relevant_tables.append(real_name)
        
        mapped_relevant_tables = list(set(mapped_relevant_tables))

        for rel in full_schemas.get("relationships", []):
            rel["source"] = table_mapping.get(rel["source"], rel["source"])
            rel["target"] = table_mapping.get(rel["target"], rel["target"])
            corrected_schemas["relationships"].append(rel)

        # 确保 pruned_schemas 始终被定义
        pruned_schemas = {
            "macro_context": corrected_schemas["macro_context"],
            "tables": {name: corrected_schemas["tables"].get(name) for name in mapped_relevant_tables if name in corrected_schemas["tables"]},
            "relationships": [r for r in corrected_schemas["relationships"] if r["source"] in mapped_relevant_tables or r["target"] in mapped_relevant_tables]
        }

        if status_callback: status_callback("🎯 正在拆解战略目标与分析路径...")
        decomposition_prompt = f"""
你是一名顶级商业技术顾问。针对用户需求，请将其拆解为 2-3 个逻辑递进的分析阶段。
需求：{query}
业务模型：{json.dumps(pruned_schemas, ensure_ascii=False)}

【关键策略】:
1. **数据依赖 (Drill Down)**：如果需求涉及深入分析（如“找出异常并分析原因”），请确保 Stage 2 的逻辑能利用 Stage 1 的产出（例如：Stage 1 找出 ID，Stage 2 使用 WHERE id IN (...)）。
2. **逻辑递进**：
   - Stage 1: 现象摸排/范围圈定 (Broad Scan)
   - Stage 2: 核心指标计算/归因 (Core Analysis)
   - Stage 3: 趋势预测/细分对比 (Optional Deep Dive)

请返回标准的 JSON 数组，格式如下：
[
  {{
    "stage_id": 1, 
    "title": "阶段标题", 
    "requirement": "【需求理解】本阶段要解决的业务核心痛点是什么",
    "transformation": "【技术转化】本阶段将如何通过数据加工（逻辑、表、指标）来满足上述需求",
    "goal": "具体执行目标", 
    "logic": "核心算法说明 (如：利用 Stage 1 产出的 user_id 列表进行二次筛选)" 
  }},
  ...
]
"""
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
            
            sample_context = ""
            for t_name in mapped_relevant_tables:
                try:
                    s_res = self.execute_sql(f"SELECT * FROM {t_name} LIMIT 2")
                    if s_res["success"] and s_res["data"]:
                        sample_context += f"- 表 '{t_name}' 数据样例: {json.dumps(s_res['data'], ensure_ascii=False)}\n"
                except: pass

            prior_context_str = ""
            if full_analysis_context:
                prior_context_str = f"\n【前序阶段分析结论 (关键上下文)】:\n{full_analysis_context}\n\n**重要指令**：如果前序结论中包含特定的 ID、日期或异常值，请务必在 SQL 的 WHERE 子句中使用它们（例如 `WHERE id IN (...)`），以实现深入分析。"

            memory_context_str = ""
            try:
                memories = self._load_memory()
                relevant_mems = []
                keywords = meta.get('logic', meta['title'])[:10] 
                for m in memories:
                    if any(k in m['query'] or k in m['goal'] for k in list(keywords)):
                        relevant_mems.append(f"- 历史参考SQL ({m['goal']}): {m['sql']}")
                if relevant_mems: memory_context_str = "\n【历史成功案例 (Few-Shot)】:\n" + "\n".join(relevant_mems[-2:]) 
            except: pass

            sql_prompt = f"""
基于分析路径："{analysis_path}"，请编写高度可读、带有详细业务注释的多方言 SQL。
业务背景：{pruned_schemas['macro_context']}
模型：{json.dumps(pruned_schemas['tables'], ensure_ascii=False)}
数据样例（请参考真实的时间格式、状态值等）：
{sample_context}
{prior_context_str}
{memory_context_str}

要求：
1. **严格限制字段与表名**：
   - **绝对禁止**使用模型中不存在的表名。
   - **严禁凭空想象字段名**。
2. **强制使用模块化编程 (CTE)**。
3. **面向小白的详细注释**。
4. **严谨的 SQL 语法 (SQLite 兼容)**。
5. 返回 JSON 对象: "dataworks", "standard", "sqlite"。
"""
            sqls = {"dataworks": "", "standard": "", "sqlite": ""}
            try:
                sql_res = model_client.complete(sql_prompt).text
                json_match = re.search(r'(\{.*\})', sql_res, re.DOTALL)
                if json_match: sqls = json.loads(json_match.group(1))
                if status_callback: status_callback(f"✅ SQL生成完毕 (覆盖 {len(sqls)} 种方言)")
            except: 
                if status_callback: status_callback("⚠️ SQL生成异常，将使用空模板")

            if status_callback: status_callback(f"🧪 [Stage {meta['stage_id']}] 正在执行逻辑验证...")
            execution_res = {"success": False, "data": []}
            is_simulated = False
            
            conn_check = sqlite3.connect(self.db_path)
            cursor_check = conn_check.cursor()
            cursor_check.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables_set = {row[0].lower() for row in cursor_check.fetchall()}
            conn_check.close()

            if sqls.get("sqlite"):
                execution_res = self.execute_sql(sqls["sqlite"], model_client=model_client)
                row_count = len(execution_res.get("data", []))
                if execution_res["success"]:
                    if status_callback: status_callback(f"⚡ [Stage {meta['stage_id']}] SQL执行成功, 命中 {row_count} 行数据")
                    if row_count > 0: self._save_memory(query=analysis_path, sql=sqls["sqlite"], goal=meta['title'])
                else:
                    if status_callback: status_callback(f"⚠️ [Stage {meta['stage_id']}] SQL执行失败: {execution_res.get('error', 'unknown')}")

                should_simulate = False
                if not execution_res["success"]:
                    should_simulate = True 
                else:
                    if row_count == 0:
                        tables_in_sql = re.findall(r'FROM\s+([a-zA-Z0-9_]+)|JOIN\s+([a-zA-Z0-9_]+)', sqls["sqlite"], re.I)
                        flat_tables = [t for group in tables_in_sql for t in group if t]
                        if any(t.lower() not in existing_tables_set for t in flat_tables): should_simulate = True 
                
                if should_simulate:
                    is_simulated = True
                    if status_callback: status_callback(f"🎲 [Stage {meta['stage_id']}] 本地数据不足，启动战略仿真模式...")
                    sim_prompt = f"【战略仿真模式】为阶段：{meta['title']} 制造 10 条趋势数据。\n背景：{pruned_schemas['macro_context']}\n表结构：{json.dumps(pruned_schemas['tables'], ensure_ascii=False)}"
                    try:
                        sim_out = model_client.complete(sim_prompt).text
                        json_match = re.search(r'(\[.*\])', sim_out, re.DOTALL)
                        if json_match: execution_res = {"success": True, "data": json.loads(json_match.group(1))}
                    except: pass
            
            stage_entry = {"meta": meta, "sqls": sqls, "data": execution_res.get("data", []), "is_simulated": is_simulated}
            if execution_res.get("success") and execution_res.get("data"):
                try:
                    df_temp = pd.DataFrame(execution_res["data"])
                    stage_entry["recommendation"] = self.recommend_visualization(query=meta["title"], columns=df_temp.columns.tolist(), sample_data=df_temp.head(3).to_dict(orient='records'), model_client=model_client)
                except: stage_entry["recommendation"] = {"viz_type": "table", "reason": "预推荐生成失败"}
            final_stages_data.append(stage_entry)
            full_analysis_context += f"阶段 {meta['stage_id']} ({meta['title']}) 结论数据: {json.dumps(stage_entry['data'][:3], ensure_ascii=False)}\n"

        if status_callback: status_callback("📝 正在撰写首席执行官战略报告...")
        summary_prompt = f"请基于推演结果撰写报告。\n需求: {query}\n摘要:\n{full_analysis_context}\n格式: SCQA架构，Bento Grid风格。"
        
        def report_generator():
            if hasattr(model_client, 'stream_chat'):
                from llama_index.core.base.llms.types import ChatMessage, MessageRole
                messages = [ChatMessage(role=MessageRole.USER, content=summary_prompt)]
                try:
                    response_gen = model_client.stream_chat(messages)
                    last_text = ""
                    for chunk in response_gen:
                        if hasattr(chunk, 'delta') and chunk.delta:
                            yield chunk.delta
                            last_text += chunk.delta
                        elif hasattr(chunk, 'message') and hasattr(chunk.message, 'content'):
                            current_text = chunk.message.content
                            if current_text.startswith(last_text):
                                delta = current_text[len(last_text):]
                                if delta:
                                    yield delta
                                    last_text = current_text
                            else:
                                yield current_text
                                last_text = current_text
                        else:
                            yield str(chunk)
                except: yield "战略推演报告生成异常"
            else:
                res = model_client.complete(summary_prompt).text
                for char in res: yield char

        def make_json_safe(obj):
            if isinstance(obj, list): return [make_json_safe(i) for i in obj]
            if isinstance(obj, dict): return {k: make_json_safe(v) for k, v in obj.items()}
            import pandas as pd
            import numpy as np
            if obj is None or pd.isna(obj): return None
            if isinstance(obj, (pd.Timestamp, datetime)): return obj.strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(obj, (int, np.integer)): return int(obj)
            if isinstance(obj, (float, np.floating)): return float(obj)
            if isinstance(obj, bytes): return obj.decode('utf-8', errors='ignore')
            return str(obj) if not isinstance(obj, (str, bool)) else obj

        return {"stages": make_json_safe(final_stages_data), "logic_gen": report_generator(), "success": True, "macro_context": pruned_schemas['macro_context']}

    def _recover_data_from_docstore(self):
        docstore_path = os.path.join(self.kb_path, "docstore.json")
        if not os.path.exists(docstore_path): return
        try:
            with open(docstore_path, 'r', encoding='utf-8') as f: docstore = json.load(f)
            nodes = docstore.get("docstore/data", {})
            import io, re
            conn = sqlite3.connect(self.db_path)
            for node_id, node_data in nodes.items():
                text = node_data.get("__data__", {}).get("text", "")
                metadata = node_data.get("__data__", {}).get("metadata", {})
                file_name = metadata.get("file_name", "")
                if file_name.endswith('.csv') or (',' in text and '\n' in text):
                    table_name = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5]', '_', os.path.splitext(file_name)[0] if file_name else f"table_{node_id[:8]}")
                    try:
                        df = pd.read_csv(io.StringIO(text))
                        df.to_sql(table_name, conn, index=False, if_exists='replace')
                    except: continue
            conn.close()
        except: pass

    def execute_sql(self, sql: str, model_client=None) -> Dict[str, Any]:
        """增强型 SQL 执行器"""
        import time
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = sqlite3.connect(self.db_path, timeout=30)
                try: conn.execute("PRAGMA journal_mode=WAL;")
                except: pass
                conn.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
                cursor = conn.cursor()
                clean_sql_block = sql.replace('\
', ' ').replace('\\', '')
                statements = [s.strip() for s in clean_sql_block.split(';') if s.strip()]
                if not statements:
                    conn.close()
                    return {"success": True, "data": []}
                rows = []
                for idx, stmt in enumerate(statements):
                    try:
                        cursor.execute(stmt)
                        if idx == len(statements) - 1 and stmt.upper().startswith("SELECT"): rows = cursor.fetchall()
                    except Exception as step_error:
                        error_msg = str(step_error).lower()
                        is_fixable = any(k in error_msg for k in ["syntax", "bindings", "no such column", "qualify", "unrecognized token", "order by"])
                        if is_fixable and model_client:
                            fix_prompt = f"Fix SQLite error: {step_error}\nSQL: {stmt}"
                            try:
                                fixed_sql = re.sub(r'```sql|```', '', model_client.complete(fix_prompt).text.strip(), flags=re.I).strip()
                                cursor.execute(fixed_sql)
                                if idx == len(statements) - 1 and fixed_sql.upper().startswith("SELECT"): rows = cursor.fetchall()
                                continue 
                            except:
                                if "SELECT" in stmt.upper(): raise step_error
                        if "SELECT" in stmt.upper(): raise step_error 
                conn.commit()
                conn.close()
                return {"success": True, "data": rows}
            except sqlite3.OperationalError as e:
                if ("locked" in str(e).lower() or "unable to open" in str(e).lower()) and attempt < max_retries - 1:
                    time.sleep(0.5)
                    continue
                return {"success": False, "error": str(e), "data": []}
            except Exception as e:
                if "no such table" in str(e).lower():
                    try:
                        self._recover_data_from_docstore()
                        return self._retry_single_query(sql) 
                    except: pass
                return {"success": False, "error": str(e), "data": []}
        return {"success": False, "error": "Max retries exceeded", "data": []}

    def _retry_single_query(self, sql: str) -> Dict[str, Any]:
        """单查询重试"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
            cursor = conn.cursor()
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            last_select = next((s for s in reversed(statements) if s.upper().startswith("SELECT")), None)
            if last_select:
                cursor.execute(last_select)
                rows = cursor.fetchall()
                conn.close()
                return {"success": True, "data": rows}
            return {"success": False, "error": "No SELECT", "data": []}
        except Exception as e: return {"success": False, "error": str(e), "data": []}

    def process_files(self, file_paths: List[str], model_client=None, status_callback=None) -> Dict[str, Any]:
        """全域开模引擎"""
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
                table_name = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5]', '_', os.path.splitext(file_name)[0])
                try:
                    if file_name.endswith('.csv'): df = pd.read_csv(file_path)
                    elif file_name.endswith(('.xls', '.xlsx')): df = pd.read_excel(file_path)
                    else: continue
                    df.columns = [re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5]', '_', str(c)) for c in df.columns]
                    df.to_sql(table_name, conn, index=False, if_exists='replace')
                    row_count = conn.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
                    if status_callback: status_callback(f"✅ 表 '{table_name}' 完成，包含 {row_count} 行数据")
                    physical_tables[table_name] = {"source": file_name, "columns": [{"name": c, "type": str(t)} for c, t in df.dtypes.items()]}
                except Exception as e:
                    if status_callback: status_callback(f"❌ 物理表 {file_name} 失败: {e}")
            conn.close()
            modeling_summary = "通用业务分析"
            if model_client and physical_tables:
                try:
                    modeling_summary = model_client.complete(f"概括这套系统的核心逻辑：{json.dumps(physical_tables, ensure_ascii=False)}").text.strip()
                except: pass
                if status_callback: status_callback(f"🧠 建模逻辑: {modeling_summary}")
            unified_schema = {"tables": physical_tables, "macro_context": modeling_summary, "relationships": []}
            if semantic_docs and model_client:
                docs_content = []
                for doc_path in semantic_docs:
                    with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f: docs_content.append(f.read()[:5000])
                prompt = f"构建统一模型。\n物理表：{json.dumps(physical_tables, ensure_ascii=False)}\n业务材料：{''.join(docs_content)}"
                try:
                    res = model_client.complete(prompt).text
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
            with open(self.schema_path, 'w', encoding='utf-8') as f: json.dump(unified_schema, f, indent=4, ensure_ascii=False)
            if model_client:
                if status_callback: status_callback("🧪 执行出厂级数据预填充...")
                self._ensure_sandbox_ready(unified_schema, model_client, status_callback=None)
            if status_callback: status_callback(f"✅ 全域建模完成: 包含 {len(unified_schema['tables'])} 张表，已持久化")
            return {"success": True, "tables": list(unified_schema['tables'].keys()), "has_virtual": any(t.get('is_virtual') for t in unified_schema['tables'].values())}
        except Exception as e: return {"success": False, "error": str(e)}