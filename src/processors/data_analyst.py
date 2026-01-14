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
        
        # [v6.3.0] 强化指令：防止“标准模型”幻觉，强制锚定输入文档
        prompt = f"""
你是一名资深首席架构师。请从以下文档中【严谨提取】业务模型与宏观背景。

【重要约束】：
1. **严禁凭空想象**：不要生成文档中未提及的表结构。严禁默认输出“产品(Products)”、“订单(Orders)”等通用电商表，除非文档中明确出现了这些业务实体。
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
        # [v5.6.6] 增强型表存在性检查 (Case-Insensitive)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0].lower() for row in cursor.fetchall()}
        
        for t_name in schemas.get('tables', {}).keys():
            # [v5.6.5] 兼容性过滤
            t_name_str = t_name[0] if isinstance(t_name, tuple) else t_name
            if "." in t_name_str or t_name_str.lower().startswith("information_schema"):
                if self.logger: self.logger.debug(f"跳过不支持的系统表: {t_name_str}")
                continue

            # 核心修复: 统一转小写对比，防止 Products != products 导致的重复生成
            if t_name_str.lower() not in existing_tables:
                tables_to_mock.append(t_name_str)
            else:
                tables_ready.append(t_name_str)
        
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
            
            # [v5.8.5] 增强型上下文注入：提供表采样数据，帮助 AI 生成准确的过滤条件
            sample_context = ""
            for t_name in relevant_table_names:
                s_res = self.execute_sql(f"SELECT * FROM {t_name} LIMIT 2")
                if s_res["success"] and s_res["data"]:
                    sample_context += f"- 表 '{t_name}' 数据样例: {json.dumps(s_res['data'], ensure_ascii=False)}\n"

            sql_prompt = f"""
基于分析路径："{analysis_path}"，请编写高度可读、带有详细业务注释的多方言 SQL。
业务背景：{pruned_schemas['macro_context']}
模型：{json.dumps(pruned_schemas['tables'], ensure_ascii=False)}
数据样例（请参考真实的时间格式、状态值等）：
{sample_context}

要求：
1. **严格限制字段与表名**：
   - **绝对禁止**使用模型中不存在的表名。
   - **严禁凭空想象字段名**：必须且仅能使用下述【模型】和【数据样例】中明确出现的列名。例如：如果样例中只有 `price` 而没有 `cost_price`，你决不能在 SQL 中使用 `cost_price`。
   - 如果需要中间结果，请使用 Common Table Expression (WITH clause)。
2. **必须包含详细的行级注释**：
   - 使用 '--' 解释每一段核心逻辑（如 FILTER, JOIN, AGGREGATE）。
   - 解释复杂的计算公式背后的业务含义。
3. **严谨的 SQL 语法**：
   - **SQLite 版本特别约束**：
     - **绝对禁止在 WHERE 子句中使用聚合函数** (如 AVG, SUM, COUNT)。如果需要基于聚合结果过滤，请使用 HAVING 子句或子查询。
     - **严禁使用 QUALIFY** 关键字。
     - **严禁使用 ? 占位符** (所有变量必须在 SQL 中直接展开为字面量)。
     - 字段名若包含特殊字符请使用双引号包裹。
4. 返回一个 JSON 对象，包含三个字段：
   - "dataworks": "生产环境 SQL (MaxCompute语法)，必须包含 ${{bizdate}} 变量"
   - "standard": "标准 ANSI SQL (用于通用数据库验证)"
   - "sqlite": "本地验证 SQL (用于当前环境执行)"

仅返回 JSON，不要有其他解释。"""
            
            # ... (原有 sqls 获取代码) ...
            sqls = {"dataworks": "", "standard": "", "sqlite": ""}
            try:
                sql_res = model_client.complete(sql_prompt).text
                import re
                json_match = re.search(r'(\{.*\})', sql_res, re.DOTALL)
                if json_match:
                    sqls = json.loads(json_match.group(1))
                if status_callback: status_callback(f"✅ SQL生成完毕 (覆盖 {len(sqls)} 种方言)")
            except: 
                if status_callback: status_callback("⚠️ SQL生成异常，将使用空模板")

            if status_callback: status_callback(f"🧪 [Stage {meta['stage_id']}] 正在执行逻辑验证...")
            execution_res = {"success": False, "data": []}
            is_simulated = False
            source_samples = {}
            
            # [v5.8.5] 获取现有表清单用于精准冲突判定
            conn_check = sqlite3.connect(self.db_path)
            cursor_check = conn_check.cursor()
            cursor_check.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables_set = {row[0].lower() for row in cursor_check.fetchall()}
            conn_check.close()

            if sqls.get("sqlite"):
                # 执行查询
                execution_res = self.execute_sql(sqls["sqlite"], model_client=model_client)
                row_count = len(execution_res.get("data", []))
                
                if execution_res["success"]:
                    if status_callback: status_callback(f"⚡ [Stage {meta['stage_id']}] SQL执行成功, 命中 {row_count} 行数据")
                else:
                    if status_callback: status_callback(f"⚠️ [Stage {meta['stage_id']}] SQL执行失败: {execution_res.get('error', 'unknown')}")

                # [v5.8.5] 核心冲突修复：只有在表确实不存在或为虚拟表时才启动仿真
                # 如果表存在但查询结果为 0，视为真实业务结论，不再“乱投医”进行仿真
                should_simulate = False
                if not execution_res["success"]:
                    should_simulate = True # 执行失败且无法修复，启用仿真保底
                else:
                    if row_count == 0:
                        # 检查涉及到的表是否在数据库中
                        # 简单正则提取表名
                        tables_in_sql = re.findall(r'FROM\s+([a-zA-Z0-9_]+)|JOIN\s+([a-zA-Z0-9_]+)', sqls["sqlite"], re.I)
                        flat_tables = [t for group in tables_in_sql for t in group if t]
                        
                        missing_any = any(t.lower() not in existing_tables_set for t in flat_tables)
                        if missing_any:
                            should_simulate = True # 确实缺表，需要仿真
                        else:
                            should_simulate = False # 表都在，只是没查到数据，保持现状
                    else:
                        should_simulate = False # 查到数据了，不仿真

                if should_simulate:
                    is_simulated = True
                    if status_callback: status_callback(f"🎲 [Stage {meta['stage_id']}] 本地数据不足，启动战略仿真模式 (生成虚拟趋势数据)...")
                    sim_prompt = f"""【战略仿真模式】为阶段：{meta['title']} 制造 10 条反映宏观趋势的“黄金模拟数据”。
业务背景：{pruned_schemas['macro_context']}
逻辑依赖：{meta['logic']}
表结构：{json.dumps(pruned_schemas['tables'], ensure_ascii=False)}

要求：
1. 数据必须逻辑闭环。
2. 仅返回 JSON 数组格式。"""
                    try:
                        sim_out = model_client.complete(sim_prompt).text
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
            
            # [v5.8.8] 智能可视化预推荐：在执行阶段就生成建议，减少 UI 延迟
            if execution_res.get("success") and execution_res.get("data"):
                try:
                    df_temp = pd.DataFrame(execution_res["data"])
                    stage_entry["recommendation"] = self.recommend_visualization(
                        query=meta["title"],
                        columns=df_temp.columns.tolist(),
                        sample_data=df_temp.head(3).to_dict(orient='records'),
                        model_client=model_client
                    )
                except:
                    stage_entry["recommendation"] = {"viz_type": "table", "reason": "预推荐生成失败"}
            final_stages_data.append(stage_entry)
            rows_count = len(stage_entry['data'])
            if status_callback: status_callback(f"📊 [Stage {meta['stage_id']}] 阶段完成: 产出 {rows_count} 条结论数据")
            full_analysis_context += f"阶段 {meta['stage_id']} ({meta['title']}) 结论数据: {json.dumps(stage_entry['data'][:3], ensure_ascii=False)}\n"

        if status_callback: status_callback("📝 正在撰写首席执行官战略报告...")
        summary_prompt = f"""
你是一名资深战略顾问（麦肯锡/波士 BCG 风格）。请基于以下【多阶段链式推演】的实际结果，采用 SCQA 架构撰写一份具备“便当盒 (Bento Grid)”布局感的首席执行官战略报告。

用户原始需求: {query}
业务宏观背景: {pruned_schemas['macro_context']}
各阶段推演数据摘要:
{full_analysis_context}

要求（严格执行）：
1. **SCQA 叙事结构**：
   - **S (Situation)**: 描述当前业务的稳定态或背景。
   - **C (Complication)**: 揭示数据中发现的矛盾、下滑、异常或瓶颈点。
   - **Q (Question)**: 提出需要决策者核心关注的 1-2 个灵魂问题。
   - **A (Answer)**: 给出基于数据的终极结论与可执行建议。

2. **Bento Grid 布局风格**：
   - 使用 Markdown 的块引用 `> ` 来突出核心指标。
   - 使用任务列表 `- [ ]` 来展示行动指南。
   - 第一段必须是 **[结论先行 (BLUF)]**，用一句话概括最关键的发现。

3. **真实性与逻辑防御**：
   - 每一个关键结论后必须标注数据来源（例如：[数据来源: Stage 1]）。
   - 严禁编造任何摘要中不存在的数据或地名。
   - 如果数据是仿真的，必须在显著位置标注：“⚠️ 极光战略沙盘模拟”。

报告模块结构：
### 🎯 核心结论 (Core Conclusion)
### 📊 业务全景 (The SCQA Context)
### 🚀 战略路线 (Action Plan)

请务必使用中文撰写完整的报告。
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

        # [v6.3.6] 最终数据序列化加固：确保所有结果均为 JSON 兼容格式
        def make_json_safe(obj):
            if isinstance(obj, list):
                return [make_json_safe(i) for i in obj]
            if isinstance(obj, dict):
                return {k: make_json_safe(v) for k, v in obj.items()}
            
            # 处理常见非序列化类型
            import pandas as pd
            import numpy as np
            
            # 1. 处理空值 (None, NaN, NaT)
            if obj is None or pd.isna(obj):
                return None
            
            # 2. 处理日期时间
            if isinstance(obj, (pd.Timestamp, datetime)):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            
            # 3. 处理数值类型 (处理 numpy 标量)
            if isinstance(obj, (int, np.integer)):
                return int(obj)
            if isinstance(obj, (float, np.floating)):
                if np.isinf(obj): return "Infinity"
                return float(obj)
            
            # 4. 处理字节
            if isinstance(obj, bytes):
                return obj.decode('utf-8', errors='ignore')
            
            # 5. 最终保底：转为字符串
            if not isinstance(obj, (str, bool)):
                return str(obj)
            
            return obj

        safe_stages = make_json_safe(final_stages_data)

        return {
            "stages": safe_stages,
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

    def execute_sql(self, sql: str, model_client=None) -> Dict[str, Any]:
        """
        [v5.7.1] 增强型 SQL 执行器：
        1. 支持多语句 (Script Mode) 并在同一事务中执行。
        2. 增加 SQL 自动修复 (Auto-Healing) 功能。
        3. [v5.7.2] 增强连接鲁棒性 (Timeout + WAL + Retry)。
        """
        import time
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # [v5.7.2] 增加超时设置，防止数据库锁定
                conn = sqlite3.connect(self.db_path, timeout=30)
                
                # [v5.7.2] 开启 WAL 模式提高并发性能
                try:
                    conn.execute("PRAGMA journal_mode=WAL;")
                except: pass
                
                # 使用 Row factory 保证结果是字典列表
                conn.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
                cursor = conn.cursor()

                # A. 预处理 [v6.3.9]: 物理剔除反斜杠干扰并按分号分割
                # LLM 经常误用 \ 作为换行符，这在 SQLite 中是非法的
                clean_sql_block = sql.replace('\\\n', ' ').replace('\\', '')
                statements = [s.strip() for s in clean_sql_block.split(';') if s.strip()]
                
                if not statements:
                    conn.close()
                    return {"success": True, "data": []}
                
                rows = []
                
                # B. 执行逻辑：顺序执行所有语句，只捕获最后一个 SELECT 的结果
                for idx, stmt in enumerate(statements):
                    try:
                        cursor.execute(stmt)
                        # 如果是最后一条语句，且是 SELECT，则获取结果
                        if idx == len(statements) - 1 and stmt.upper().startswith("SELECT"):
                            rows = cursor.fetchall()
                    except Exception as step_error:
                        # [v5.7.1] 自动修复逻辑
                        error_msg = str(step_error).lower()
                        
                        # 仅在模型可用且错误类型可修复时触发
                        is_fixable = any(k in error_msg for k in ["syntax", "bindings", "no such column", "qualify", "unrecognized token", "order by"])
                        
                        if is_fixable and model_client:
                            if self.logger: self.logger.warning(f"🔧 SQL执行报错，尝试自动修复: {error_msg}")
                            fix_prompt = f"""
【致命错误修复请求】
当前的 SQLite 语句执行失败。请根据报错信息，重新编写一条正确的 SQL。

错误信息: {step_error}
原始 SQL: {stmt}

【必须遵守的修正准则】：
1. **严禁在 WHERE 子句中使用聚合函数**：如发现 `WHERE AVG(...)` 或 `WHERE SUM(...)`，必须将其移至 `HAVING` 子句中，或者改用子查询。
2. **语法校对**：检查 `IS`、`LIKE` 等操作符是否符合 SQLite 语法（例如：IS NULL, NOT NULL）。
3. **字段保护**：确保所有字段名与模型完全一致。
4. **格式要求**：仅输出修复后的 SQL 语句，严禁包含任何 Markdown 格式或解释说明。
"""
                            try:
                                fixed_sql_res = model_client.complete(fix_prompt).text.strip()
                                # 彻底清理可能存在的 Markdown
                                fixed_sql = re.sub(r'```sql|```', '', fixed_sql_res, flags=re.I).strip()
                                
                                cursor.execute(fixed_sql)
                                if idx == len(statements) - 1 and fixed_sql.upper().startswith("SELECT"):
                                    rows = cursor.fetchall()
                                if self.logger: self.logger.success(f"✅ SQL自动修复成功")
                                continue # 修复成功，继续下一条
                            except Exception as fix_err:
                                if self.logger: self.logger.error(f"❌ 自动修复失败: {fix_err}")
                                if "SELECT" in stmt.upper(): raise step_error

                        # 默认行为：如果不是 SELECT，可能是 DROP/CREATE 失败，尝试忽略；如果是 SELECT 失败则抛出
                        if "SELECT" in stmt.upper():
                            raise step_error 
                
                conn.commit()
                conn.close()
                return {"success": True, "data": rows}
                
            except sqlite3.OperationalError as e:
                # [v5.7.2] 捕获文件锁定或无法打开的错误并重试
                error_str = str(e).lower()
                if "locked" in error_str or "unable to open" in error_str:
                    if attempt < max_retries - 1:
                        if self.logger: self.logger.warning(f"⚠️ 数据库忙或被锁定，正在重试 ({attempt+1}/{max_retries})...")
                        time.sleep(0.5)
                        continue
                
                # 无法恢复的错误，返回失败
                return {"success": False, "error": str(e), "data": []}
                
            except Exception as e:
                error_str = str(e)
                # 自动修复机制：如果表不存在，尝试从 docstore 恢复
                if "no such table" in error_str.lower():
                    try:
                        self._recover_data_from_docstore()
                        # 恢复后重试（递归调用一次）
                        return self._retry_single_query(sql) 
                    except: pass
                
                return {"success": False, "error": str(e), "data": []}
        
        return {"success": False, "error": "Max retries exceeded", "data": []}

    def _retry_single_query(self, sql: str) -> Dict[str, Any]:
        """简单的单查询重试"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = lambda c, r: dict([(col[0], r[idx]) for idx, col in enumerate(c.description)])
            cursor = conn.cursor()
            # 这里的 sql 可能是多语句，所以简单分割取最后一条
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            last_select = next((s for s in reversed(statements) if s.upper().startswith("SELECT")), None)
            
            if last_select:
                cursor.execute(last_select)
                rows = cursor.fetchall()
                conn.close()
                return {"success": True, "data": rows}
            return {"success": False, "error": "No SELECT found in retry", "data": []}
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}

    def process_files(self, file_paths: List[str], model_client=None, status_callback=None) -> Dict[str, Any]:
        """
        [v5.3 战略版] 全域开模引擎：支持全格式输入 (PDF/MD/CSV/XLSX) 统一建模。
        """
        import re
        try:
            if self.logger: self.logger.info(f"🏗️ 开始构建业务数据库: {self.db_path}")
            
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
                    if self.logger: self.logger.info(f"📥 正在导入表 '{table_name}' (来源: {file_name})...")
                    
                    if file_name.endswith('.csv'): df = pd.read_csv(file_path)
                    elif file_name.endswith(('.xls', '.xlsx')): df = pd.read_excel(file_path)
                    else: continue
                    
                    df.columns = [re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5]', '_', str(c)) for c in df.columns]
                    df.to_sql(table_name, conn, index=False, if_exists='replace')
                    
                    # [v5.8.1] 立即验证导入结果
                    row_count = conn.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
                    msg = f"✅ 表 '{table_name}' 构建完成，包含 {row_count} 行数据"
                    if self.logger: self.logger.success(msg)
                    if status_callback: status_callback(msg)
                    
                    physical_tables[table_name] = {
                        "source": file_name,
                        "columns": [{"name": c, "type": str(t)} for c, t in df.dtypes.items()]
                    }
                except Exception as e:
                    err_msg = f"❌ 物理表 {file_name} 解析失败: {e}"
                    if self.logger: self.logger.warning(err_msg)
                    if status_callback: status_callback(err_msg)
            
            conn.close()

            # [v6.5.5] 生成建模逻辑摘要：让用户知道系统是如何理解这批数据的
            modeling_summary = "通用业务分析"
            if self.logger and model_client:
                t_list = list(physical_tables.keys())
                summary_prompt = f"请根据这组物理表名及其字段，用一句话概括这套业务系统的核心逻辑：{json.dumps(physical_tables, ensure_ascii=False)}"
                try:
                    modeling_summary = model_client.complete(summary_prompt).text.strip()
                except: pass
                
                msg = f"🧠 建模逻辑确认: {modeling_summary}\\n📂 构建业务表清单: {', '.join(t_list)}"
                if self.logger: self.logger.success(msg)
                if status_callback: status_callback(msg)

            unified_schema = {
                "tables": physical_tables, 
                "macro_context": modeling_summary, 
                "relationships": []
            }
            
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

**CRITICAL**: 如果【业务材料】中的表名与【物理表结构】中的表名不同（例如 users vs Customers），**必须强制使用【物理表结构】中的表名**（如 users）。严禁修改已存在的物理表名。
**CRITICAL**: 仅当【业务材料】中提到的表完全不存在于【物理表结构】中时，才可将其定义为新表（is_virtual=true）。不要添加非必要的虚拟表。
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