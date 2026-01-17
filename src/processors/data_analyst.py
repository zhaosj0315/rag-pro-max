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
        if not all_tables: return []
        
        # 原则：数据分析模式下，优先保证完整性。
        # 如果表数量不多（<15），直接返回所有表，确保跨表查询和元数据查询的准确性。
        if len(all_tables) <= 15:
            return list(all_tables.keys())
            
        # 仅在表极其多的时候进行简单过滤
        relevant = []
        qw = query.lower()
        for t in all_tables:
            if t.lower() in qw:
                relevant.append(t)
        
        return list(set(relevant)) if relevant else list(all_tables.keys())[:10]

    def _get_column_value_samples(self, table_name: str, conn: sqlite3.Connection) -> str:
        try:
            cursor = conn.cursor()
            # 转义表名
            safe_table = f'"{table_name}"'
            cursor.execute(f"PRAGMA table_info({safe_table})")
            cols = [row[1] for row in cursor.fetchall()]
            samples = []
            for col in cols:
                if any(k in col.lower() for k in ['status', 'type', 'category', 'region', 'gender', 'state', '状态', '类型', '渠道']):
                    # 转义列名
                    safe_col = f'"{col}"'
                    cursor.execute(f"SELECT DISTINCT {safe_col} FROM {safe_table} LIMIT 5")
                    vals = [str(row[0]) for row in cursor.fetchall() if row[0] is not None]
                    if vals: samples.append(f"字段 '{col}' 取值范围: {vals}")
            return "\n".join(samples)
        except: return ""

    def _generate_mock_data(self, table_name: str, table_info: Dict, schemas: Dict, model_client, cursor) -> bool:
        """生成虚拟数据并插入表中"""
        try:
            cols = table_info.get('cols', table_info.get('columns', []))
            if not cols:
                return False
            
            # 归一化 cols 格式: 确保每个元素都是 dict 且包含 'name'
            normalized_cols = []
            for c in cols:
                if isinstance(c, dict) and 'name' in c:
                    normalized_cols.append(c)
                elif isinstance(c, str):
                    normalized_cols.append({"name": c, "type": "TEXT", "comment": ""})
            
            if not normalized_cols: return False
            cols = normalized_cols

            # 构建表结构
            col_defs = []
            for c in cols:
                col_name = c['name']
                col_type = str(c.get('type', 'TEXT'))
                # 映射常见类型到 SQLite 类型
                if any(k in col_type.upper() for k in ['INT', 'NUM', 'DECIMAL', 'FLOAT']):
                    sql_type = 'REAL'
                elif any(k in col_type.upper() for k in ['DATE', 'TIME']):
                    sql_type = 'TEXT'
                else:
                    sql_type = 'TEXT'
                col_defs.append(f'"{col_name}" {sql_type}')
            
            # 创建表 (使用引号转义表名)
            safe_table = f'"{table_name}"'
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {safe_table} ({', '.join(col_defs)})")
            
            # 生成数据的提示词
            cols_desc = "\n".join([f"- {c['name']}: {c.get('comment', c.get('type', 'TEXT'))}" for c in cols])
            macro_context = schemas.get('macro_context', '业务数据')
            table_desc = table_info.get('desc', table_name)
            
            prompt = f"""为数据表 '{table_name}' 生成 30 条真实、合理的测试数据。

表说明: {table_desc}
业务背景: {macro_context}

字段定义:
{cols_desc}

要求:
1. 生成标准的 SQLite INSERT 语句
2. 数据要符合业务逻辑，相互关联
3. 日期格式: YYYY-MM-DD，时间格式: YYYY-MM-DD HH:MM:SS
4. 数值字段使用纯数字，不要带单位
5. 每条语句独立一行，以分号结尾
6. 只输出 INSERT 语句，不要其他内容

示例格式:
INSERT INTO {table_name} VALUES ('value1', 'value2', 123);
INSERT INTO {table_name} VALUES ('value3', 'value4', 456);"""

            print(f"🎲 [虚拟数据] 正在为表 '{table_name}' 生成测试数据...")
            
            try:
                response = model_client.complete(prompt).text
                print(f"   📝 LLM 返回长度: {len(response)} 字符")
            except Exception as e:
                print(f"   ❌ LLM 调用失败: {e}")
                print(f"   🔄 直接使用备用方案...")
                return self._generate_simple_mock_data(table_name, cols, cursor)
            
            # 提取并执行 INSERT 语句
            insert_count = 0
            # 使用正则匹配完整的 INSERT 语句
            statements = re.findall(r'INSERT\s+INTO\s+.*?;', response, re.DOTALL | re.IGNORECASE)
            
            if not statements:
                # 尝试按行提取 (兼容没有分号的情况)
                for line in response.split('\n'):
                    line = line.strip()
                    if line.upper().startswith('INSERT INTO'):
                        if not line.endswith(';'): line += ';'
                        statements.append(line)

            for clean_stmt in statements:
                try:
                    # 清理可能的 markdown 代码块标记
                    clean_stmt = clean_stmt.replace('```sql', '').replace('```', '').strip()
                    cursor.execute(clean_stmt)
                    insert_count += 1
                except Exception as e:
                    # 如果是因为字段不匹配，尝试通过列名显式插入
                    try:
                        # 这是一个极具侵略性的自愈尝试：如果 LLM 返回的语句列数不对，尝试丢弃
                        pass
                    except: pass
                    continue
            
            if insert_count > 0:
                print(f"✅ [虚拟数据] 表 '{table_name}' 成功生成 {insert_count} 条记录")
                return True
            else:
                print(f"⚠️ [虚拟数据] 表 '{table_name}' LLM 生成失败（0条），尝试备用方案...")
                return self._generate_simple_mock_data(table_name, cols, cursor)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"生成虚拟数据致命错误: {e}")
            return False

    def _generate_simple_mock_data(self, table_name: str, cols: List[Dict], cursor) -> bool:
        """生成简单的占位数据（备用方案）"""
        try:
            print(f"   🔄 [备用方案] 开始为表 '{table_name}' 生成占位数据...")
            # 确保 cols 元素是 dict
            normalized_cols = []
            for c in cols:
                if isinstance(c, dict): normalized_cols.append(c)
                else: normalized_cols.append({"name": str(c)})
            cols = normalized_cols

            placeholders = ', '.join(['?' for _ in cols])
            safe_table = f'"{table_name}"'
            
            insert_count = 0
            for i in range(20):
                values = []
                for c in cols:
                    col_name = str(c.get('name', '')).lower()
                    col_type = str(c.get('type', 'TEXT')).upper()
                    
                    # 根据字段名和类型生成合理的值
                    if 'id' in col_name:
                        values.append(f"ID{i+1:04d}")
                    elif any(k in col_name for k in ['name', '名称', '姓名']):
                        values.append(f"测试{i+1}")
                    elif any(k in col_name for k in ['date', '日期', 'time', '时间']):
                        values.append(f"2025-01-{(i%28)+1:02d}")
                    elif any(k in col_name for k in ['amount', 'price', 'sales', '金额', '价格', '销售']):
                        values.append(str((i+1) * 1000 + (i*137) % 1000))
                    elif any(k in col_name for k in ['status', '状态']):
                        values.append(['正常', '待审核', '已完成'][i % 3])
                    elif any(k in col_name for k in ['province', '省份', 'region', '地区']):
                        values.append(['广东', '上海', '北京', '江苏', '浙江'][i % 5])
                    elif any(k in col_name for k in ['industry', '行业']):
                        values.append(['信息技术', '医疗健康', '金融服务', '制造业'][i % 4])
                    elif any(k in col_name for k in ['product', '产品']):
                        values.append(['笔记本电脑', '手机', '平板电脑', '键盘', '鼠标'][i % 5])
                    elif any(k in col_name for k in ['customer', '客户']):
                        values.append(['张三', '李四', '王五', '赵六', '钱七'][i % 5])
                    elif 'INT' in col_type or 'NUM' in col_type or 'REAL' in col_type:
                        values.append(str((i+1) * 100))
                    else:
                        values.append(f"数据{i+1}")
                
                try:
                    cursor.execute(f"INSERT INTO {safe_table} VALUES ({placeholders})", values)
                    insert_count += 1
                except Exception as e:
                    continue
            
            if insert_count > 0:
                print(f"✅ [虚拟数据] 表 '{table_name}' 使用备用方案生成 {insert_count} 条记录")
                return True
            else:
                print(f"❌ [虚拟数据] 表 '{table_name}' 备用方案失败")
                return False
        except Exception as e:
            return False

    def _ensure_sandbox_ready(self, schemas: Dict[str, Any], model_client, status_callback=None, target_tables: List[str] = None, conn=None) -> Dict[str, str]:
        should_close = False
        if conn is None:
            conn = sqlite3.connect(self.db_path)
            should_close = True
        
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS dual (dummy TEXT)")
        res = cursor.execute("SELECT count(*) FROM dual").fetchone()
        # 兼容 row_factory 返回 dict 的情况
        count = res[0] if isinstance(res, (tuple, list)) else list(res.values())[0]
        if not count:
            cursor.execute("INSERT INTO dual VALUES ('X')")
        
        table_mapping = {}
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        real_tables = {row[0] if isinstance(row, (tuple, list)) else list(row.values())[0].lower(): (row[0] if isinstance(row, (tuple, list)) else list(row.values())[0]) for row in cursor.fetchall()}
        
        def find_match(name):
            n = name.lower()
            if n in real_tables: return real_tables[n]
            if n + 's' in real_tables: return real_tables[n+'s']
            if n.endswith('s') and n[:-1] in real_tables: return real_tables[n[:-1]]
            for k in [f"t_{n}", f"{n}_info", f"raw_{n}"]:
                if k in real_tables: return real_tables[k]
            return None

        check_list = target_tables if target_tables else list(schemas.get('tables', {}).keys())
        tables_need_data = []
        
        for t in check_list:
            if t.lower() in ('dual', 'sqlite_sequence') or "." in t: 
                continue
            
            match = find_match(t)
            if match:
                # 表存在，检查是否有数据
                try:
                    row_count = cursor.execute(f'SELECT count(*) FROM "{match}"').fetchone()[0]
                    if row_count > 0:
                        table_mapping[t] = match
                        print(f"✅ [数据检查] 表 '{match}' 已有 {row_count} 条数据")
                        continue
                    else:
                        print(f"⚠️ [数据检查] 表 '{match}' 为空，需要生成虚拟数据")
                        tables_need_data.append((t, match))
                except Exception as e:
                    tables_need_data.append((t, match))
            else:
                # 表不存在，如果是 virtual 或者是 target 则需要创建
                print(f"⚠️ [数据检查] 表 '{t}' 不存在，需要创建并生成虚拟数据")
                tables_need_data.append((t, t))

        # 生成虚拟数据
        if tables_need_data and model_client:
            if status_callback: 
                status_callback(f"🎲 正在为 {len(tables_need_data)} 个表生成虚拟数据...")
            
            # 先寻找对应的 schema 定义
            schema_tables = {k.lower(): k for k in schemas.get('tables', {}).keys()}
            
            for schema_name, physical_name in tables_need_data:
                orig_key = schema_tables.get(schema_name.lower())
                if orig_key:
                    table_info = schemas['tables'][orig_key]
                    if self._generate_mock_data(physical_name, table_info, schemas, model_client, cursor):
                        table_mapping[schema_name] = physical_name
                        conn.commit()
        
        if should_close: 
            conn.close()
        return table_mapping

    def extract_schema_from_docs(self, docs: List[Any], model_client, status_callback=None) -> Dict[str, Any]:
        """从文档中提取 Schema (供 apppro 调用)"""
        if not docs: return {}
        if status_callback: status_callback("🔍 正在从业务文档中深度提取表结构定义...")
        
        all_text = "\n".join([str(d.get_text() if hasattr(d, 'get_text') else getattr(d, 'text', '')) for d in docs[:20]])
        if len(all_text) > 30000: all_text = all_text[:30000] + "..."
        
        prompt = f"""分析以下业务材料，提取其中涉及的所有数据表定义。

业务材料：
{all_text}

要求：
1. 识别所有提到的实体/表名
2. 提取每个表的字段定义（字段名、类型、说明）
3. 推断表之间的关联关系
4. 返回标准 JSON 格式

返回格式：
{{
  "macro_context": "业务背景描述",
  "tables": {{
    "表名": {{
      "desc": "表说明",
      "cols": [
        {{"name": "字段名", "type": "类型", "comment": "说明"}}
      ]
    }}
  }}
}}

只返回 JSON，不要其他内容。"""
        
        try:
            res = model_client.complete(prompt).text
            match = re.search(r'(\{.*\})', res, re.DOTALL)
            if match:
                new_schema = json.loads(match.group(1))
                # 合并到现有 schema
                if os.path.exists(self.schema_path):
                    with open(self.schema_path, 'r', encoding='utf-8') as f:
                        current = json.load(f)
                else:
                    current = {"tables": {}, "macro_context": ""}
                
                # 合并 tables
                for t, info in new_schema.get('tables', {}).items():
                    if t not in current['tables']:
                        current['tables'][t] = info
                        current['tables'][t]['is_virtual'] = True
                    else:
                        current['tables'][t].update(info)
                
                if new_schema.get('macro_context'):
                    current['macro_context'] = new_schema['macro_context']
                
                with open(self.schema_path, 'w', encoding='utf-8') as f:
                    json.dump(current, f, indent=4, ensure_ascii=False)
                
                if status_callback: status_callback(f"✅ 成功从文档提取了 {len(new_schema.get('tables', {}))} 个逻辑表定义")
                return current
        except Exception as e:
            if status_callback: status_callback(f"⚠️ 从文档提取 Schema 失败: {e}")
        return {}

    def recommend_visualization(self, query: str, columns: List[str], sample_data: List[Dict], model_client) -> Dict[str, Any]:
        """智能可视化推荐 (供 apppro 调用)"""
        prompt = f"""你是一名资深数据可视化专家。请根据用户的查询意图和数据特征，推荐最适合的可视化方案。

用户查询: {query}
数据字段: {columns}
数据样例: {json.dumps(sample_data, ensure_ascii=False)}

请从以下类型中选择一种最能洞察数据的图表: 
["bar", "line", "pie", "scatter", "area", "table"]

返回标准 JSON 格式:
{{
  "viz_type": "推荐的类型",
  "x_axis": "X轴字段名",
  "y_axis": "Y轴字段名",
  "color": "颜色/分组字段名 (可选)",
  "title": "图表标题",
  "reason": "推荐理由"
}}
"""
        try:
            res = model_client.complete(prompt).text
            match = re.search(r'(\{.*\})', res, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        except: pass
        return {"viz_type": "table"}

    def execute_analysis(self, query: str, model_client, context_text: str = "", status_callback=None) -> Dict[str, Any]:
        # --- 终端强制输出: 任务启动 ---
        print("\n" + "="*60)
        print(f"🚀 [Strategic Workshop] 接收到分析请求: {query}")
        print("="*60)
        
        if not os.path.exists(self.schema_path): 
            print("❌ [错误] 架构文件不存在，尝试创建默认架构...")
            # 创建一个最小的默认架构
            default_schema = {
                "macro_context": "业务数据分析系统",
                "tables": {}
            }
            with open(self.schema_path, 'w', encoding='utf-8') as f:
                json.dump(default_schema, f, indent=4, ensure_ascii=False)
            print("⚠️ [警告] 已创建默认架构，但没有表定义")
            
        with open(self.schema_path, 'r', encoding='utf-8') as f: full_schemas = json.load(f)
        
        # 检查是否有表定义
        if not full_schemas.get('tables'):
            print("⚠️ [警告] Schema 中没有表定义，无法进行数据分析")
            print("💡 [提示] 请确保：")
            print("   1. 上传了 CSV/Excel 文件，或")
            print("   2. 提供了包含表结构的文档，或")
            print("   3. 手动创建了 business_schema.json")
            
            # 返回一个友好的错误提示
            def error_gen():
                yield "抱歉，当前知识库中没有找到数据表定义。\n\n"
                yield "要使用数据分析功能，您需要：\n"
                yield "1. 上传包含数据的 CSV 或 Excel 文件，或\n"
                yield "2. 提供包含表结构定义的文档（Markdown/文本），或\n"
                yield "3. 在知识库目录中创建 business_schema.json 文件\n\n"
                yield "如果您已经上传了文件，请确保文件格式正确，并重新构建知识库。"
            
            return {
                "stages": [],
                "logic_gen": error_gen(),
                "success": False,
                "macro_context": "无表定义"
            }
        
        # 1. 元数据与架构咨询直查 (Bypass SQL Engine for Consultation)
        metadata_keywords = [
            "指标", "结构", "字典", "有哪些表", "字段", "属性", "field", "column", "table", "schema", "definition", "mandatory", "required", 
            "架构", "建议", "方案", "流程", "监控", "etl", "elt", "architecture", "strategy", "workflow", "monitor",
            "配置", "设置", "调优", "怎么", "如何", "实现", "路径", "config", "settings", "optimize", "how", "implement", "pipeline"
        ]
        if any(k in query.lower() for k in metadata_keywords):
            print(f"🔍 [决策] 判定为架构/配置咨询，构建深度透视看板...")
            
            # 识别相关表以提供上下文
            rel_tables = self._get_relevant_tables(query, full_schemas)
            sub_schema = {t: full_schemas['tables'][t] for t in rel_tables if t in full_schemas['tables']}
            
            # 构造回显表格
            schema_rows = []
            for t, info in sub_schema.items():
                cols = info.get('cols', info.get('columns', []))
                for c in cols:
                    schema_rows.append({
                        "业务实体": t,
                        "关联字段": c.get('name'),
                        "业务逻辑/含义": c.get('comment', '业务默认属性')
                    })
            
            def report_gen():
                p = f"执行深度战略咨询任务。需求: {query}\n当前业务底座模型: {json.dumps(sub_schema, ensure_ascii=False)}\n要求: 采用 SCQA 架构，结合底座字段给出具体的工程落地建议、配置参数或架构设计图描述，结论先行。"
                if hasattr(model_client, 'stream_chat'):
                    from llama_index.core.base.llms.types import ChatMessage, MessageRole
                    try:
                        for chunk in model_client.stream_chat([ChatMessage(role=MessageRole.USER, content=p)]):
                            yield chunk.delta if hasattr(chunk, 'delta') else str(chunk)
                    except: yield "生成异常"
                else: yield model_client.complete(p).text

            # 构造透视阶段，确保 UI 看板不为空
            consultation_stage = {
                "meta": {"stage_id": 1, "title": "全域战略/架构透视", "goal": "对齐业务逻辑与物理底座实现路径"},
                "sqls": {
                    "sqlite": "-- 战略推演模式 (Strategic Architectural Inference)\n-- 当前问题侧重于架构/配置建议，已提取相关业务模型作为设计依据",
                    "standard": "-- Recommended Implementation Logic"
                },
                "data": schema_rows if schema_rows else [{"状态": "已完成逻辑建模", "可参考实体": list(full_schemas.get('tables', {}).keys())}],
                "empty_reason": "",
                "source_samples": {},
                "is_simulated": True
            }
            
            return {
                "stages": [consultation_stage], 
                "logic_gen": report_gen(), 
                "success": True, 
                "macro_context": full_schemas.get('macro_context', "战略咨询")
            }

        # 2. 识别与对齐
        rel_tables = self._get_relevant_tables(query, full_schemas)
        print(f"📁 [建模] 锁定业务范围: {rel_tables}")
        
        session_conn = sqlite3.connect(self.db_path, timeout=60)
        try:
            # 原则：如果是数据分析模式，且涉及范围内的表在数据库中不存在或为空，必须先完成“无数造数”的闭环
            if status_callback: status_callback("🛡️ 正在确保业务底座完整性...")
            mapping = self._ensure_sandbox_ready(full_schemas, model_client, status_callback, rel_tables, conn=session_conn)
            
            # 重新获取子架构（使用映射后的物理表名）
            sub_schema = {}
            for t in rel_tables:
                if t in full_schemas['tables']:
                    phys_name = mapping.get(t, t)
                    sub_schema[phys_name] = full_schemas['tables'][t]

            # 3. 任务拆解
            print("🎯 [规划] 正在拆解战略目标与分析路径...")
            prompt = f"将需求 {query} 拆解为 2-3 个 SQL 阶段。JSON 数组: [{{stage_id, title, transformation, goal}}]\n模型: {json.dumps(sub_schema, ensure_ascii=False)}"
            try:
                res = model_client.complete(prompt).text
                stages_meta = json.loads(re.search(r'(\[.*\])', res, re.DOTALL).group(1))
                for s in stages_meta:
                    print(f"   📍 Stage {s['stage_id']}: {s['title']} | 目标: {s['goal']}")
            except: 
                stages_meta = [{"stage_id": 1, "title": "数据透视", "transformation": "执行分析"}]

            final_data = []
            analysis_context = ""
            for i, meta in enumerate(stages_meta):
                print(f"\n--- ⏳ 执行阶段 {i+1}: {meta.get('title')} ---")
                if status_callback: status_callback(f"⚙️ [Stage {i+1}] 正在精准对齐数据...")
                
                t_context = {}
                for t in sub_schema:
                    info = sub_schema[t]
                    cols = info.get('cols', info.get('columns', []))
                    keep = ['status', 'state', 'date', 'time', 'amount', 'price', 'total', 'id', 'name', '合规', '成本', '延迟', '影响', '率']
                    filtered = [c for c in cols if any(k in c['name'].lower() or k in str(c.get('comment','')).lower() for k in keep)]
                    val_samples = self._get_column_value_samples(t, session_conn)
                    if val_samples: print(f"📊 [指纹] 表 '{t}' 真实取值: {val_samples.replace('\n', ' | ')}")
                    
                    t_context[t] = {
                        "desc": info.get("desc"), 
                        "cols": filtered if filtered else cols[:10],
                        "value_samples": val_samples
                    }
                    try:
                        # 采样更多数据用于展示和分析
                        r = self.execute_sql(f'SELECT * FROM "{t}" LIMIT 5', conn=session_conn)
                        if r["success"] and r["data"]: 
                            t_context[t]["sample"] = r['data']  # 存储多行数据
                            t_context[t]["sample_count"] = len(r['data'])
                    except: pass

                sql_prompt = f"""
编写分析 SQL 任务: {meta.get('transformation')}

表结构与真实数据样例:
{json.dumps(t_context, ensure_ascii=False)}

前序分析结果:
{analysis_context}

【关键约束】:
1. 必须使用表中实际存在的字段名和取值
2. 如果看到 value_samples（真实取值范围），必须使用这些实际值，不要假设其他值
3. 不要使用参数占位符（如 :start_date），直接使用具体的值或函数
4. 不要假设数据格式（如分隔符），使用实际的数据格式
5. 如果没有时间限制，不要添加 WHERE 时间条件

【返回格式】:
返回标准 JSON: {{"sqlite": "...", "standard": "...", "dataworks": "..."}}
只返回 JSON，不要其他内容。
"""
                sqls = {"sqlite": ""}
                try:
                    sqls = self._extract_json(model_client.complete(sql_prompt).text) or {"sqlite": ""}
                    if sqls.get('sqlite'):
                        print(f"📜 [SQL] {sqls['sqlite']}")
                except: pass

                if status_callback: status_callback(f"🧪 [Stage {i+1}] 执行逻辑验证...")
                exec_res = {"success": False, "data": []}
                empty_reason = "该阶段执行了逻辑加工，未产生回显数据"
                
                if sqls.get("sqlite"):
                    exec_res = self.execute_sql(sqls["sqlite"], model_client, conn=session_conn)
                    if exec_res["success"]:
                        if exec_res['data']:
                            r_count = len(exec_res['data'])
                            print(f"✅ [结果] 成功命中 {r_count} 行记录")
                            if status_callback: status_callback(f"✅ 命中 {r_count} 行数据")
                            analysis_context += f"阶段{i+1}: {json.dumps(exec_res['data'][:5], ensure_ascii=False)}\n"
                            empty_reason = ""
                        else:
                            # 强化正则：支持引号、空格和 TEMPORARY 关键字
                            m_table = re.search(r'CREATE\s+(?:TEMPORARY\s+)?TABLE\s+(?:"?)([a-zA-Z0-9_]+)(?:"?)', sqls["sqlite"], re.I)
                            if m_table:
                                t_name = m_table.group(1)
                                print(f"🏗️ [探测] 识别到新产生的临时实体: {t_name}")
                                
                                # 强制物理探测
                                v_res = self.execute_sql(f'SELECT * FROM "{t_name}" LIMIT 10', conn=session_conn)
                                if v_res["success"] and v_res["data"]:
                                    exec_res["data"] = v_res["data"]
                                    print(f"✅ [采样] 表 '{t_name}' 已就绪并成功采样 {len(v_res['data'])} 行")
                                    empty_reason = ""
                                else:
                                    empty_reason = f"🏗️ 阶段执行成功，但新实体 '{t_name}' 内无数据回显"
                            else:
                                # 检查是否有 SELECT 语句但结果为空
                                if "SELECT" in sqls["sqlite"].upper():
                                    empty_reason = "⚠️ 查询执行成功，但当前筛选条件下无符合记录"
                                else:
                                    empty_reason = "🏗️ 逻辑加工已完成（无回显数据产生）"
                
                final_data.append({
                    "meta": meta, "sqls": sqls, "data": exec_res["data"], 
                    "empty_reason": empty_reason,
                    "source_samples": {t: t_context[t].get('sample', {}) for t in t_context},
                    "is_simulated": is_simulated
                })

            print("\n" + "-"*60)
            print("🧠 [总结] 正在合成最终战略洞察报告...")
            print("-"*60 + "\n")
            
            def report_gen():
                p = f"撰写战略报告。需求: {query}\n结论: {analysis_context}\n要求: SCQA 架构，结论先行。"
                if hasattr(model_client, 'stream_chat'):
                    from llama_index.core.base.llms.types import ChatMessage, MessageRole
                    try:
                        for chunk in model_client.stream_chat([ChatMessage(role=MessageRole.USER, content=p)]):
                            yield chunk.delta if hasattr(chunk, 'delta') else str(chunk)
                    except: yield "生成异常"
                else: yield model_client.complete(p).text

            # 归一化与安全化处理 (Normalization & Serialization Safety)
            def sanitize_stage(s):
                # 1. 强制 Key 归一化 (sqlite, standard, dataworks)
                raw_sqls = s.get("sqls", {})
                normalized_sqls = {str(k).lower().strip(): v for k, v in raw_sqls.items()}
                
                # 2. 补全缺失的 SQL 视角
                if 'sqlite' not in normalized_sqls and normalized_sqls:
                    normalized_sqls['sqlite'] = list(normalized_sqls.values())[0] # 拿第一个当保底
                
                # 3. 强制数据安全化 (解决 NumPy 序列化问题)
                raw_rows = s.get("data", [])
                safe_rows = []
                if isinstance(raw_rows, list):
                    for row in raw_rows:
                        if isinstance(row, dict):
                            safe_row = {}
                            for k, v in row.items():
                                if pd.isna(v): safe_row[k] = None
                                elif hasattr(v, 'item'): safe_row[k] = v.item() # NumPy types
                                elif isinstance(v, (datetime, pd.Timestamp)): safe_row[k] = v.isoformat()
                                else: safe_row[k] = v
                            safe_rows.append(safe_row)
                        else: safe_rows.append(row)
                
                return {
                    "meta": s.get("meta", {"stage_id": 99, "title": "未命名阶段"}),
                    "sqls": normalized_sqls,
                    "data": safe_rows,
                    "empty_reason": s.get("empty_reason", ""),
                    "source_samples": s.get("source_samples", {}),
                    "is_simulated": s.get("is_simulated", False)
                }

            final_stages_sanitized = [sanitize_stage(s) for s in final_data]

            return {
                "stages": final_stages_sanitized, 
                "logic_gen": report_gen(), 
                "success": True, 
                "macro_context": full_schemas.get('macro_context','')
            }
        finally:
            session_conn.close()

    def execute_sql(self, sql: str, model_client=None, conn=None) -> Dict[str, Any]:
        should_close = False
        if conn is None:
            conn = sqlite3.connect(self.db_path, timeout=30)
            should_close = True
        try:
            cursor = conn.cursor()
            clean_sql = sql.replace('\n', ' ').replace('```sql', '').replace('```', '').strip()
            statements = [s.strip() for s in clean_sql.split(';') if s.strip()]
            
            final_rows = []
            # 记录是否已经抓取到了有效结果
            has_result = False
            
            QUERY_STARTERS = ("SELECT", "WITH", "VALUES", "PRAGMA", "EXPLAIN")
            for stmt in statements:
                if not stmt: continue
                try:
                    cursor.execute(stmt)
                    clean_stmt = re.sub(r'^(\s*(--.*|/\*.*?\*/)\s*)+', '', stmt, flags=re.MULTILINE).strip()
                    
                    # 只要是查询语句，就尝试抓取结果
                    if any(clean_stmt.upper().startswith(s) for s in QUERY_STARTERS):
                        raw_data = cursor.fetchall()
                        if cursor.description:
                            cols = [col[0] for col in cursor.description]
                            current_rows = [dict(zip(cols, r)) for r in raw_data]
                            # 策略：保留最新的有效非空结果集
                            if current_rows:
                                final_rows = current_rows
                                has_result = True
                except Exception as e:
                    if model_client:
                        try:
                            fix = model_client.complete(f"修正 SQL: {e}\nSQL: {stmt}").text
                            fixed_stmt = fix.replace('```sql', '').replace('```', '').strip()
                            cursor.execute(fixed_stmt)
                            if any(fixed_stmt.upper().startswith(s) for s in QUERY_STARTERS):
                                raw_data = cursor.fetchall()
                                if cursor.description:
                                    cols = [col[0] for col in cursor.description]
                                    final_rows = [dict(zip(cols, r)) for r in raw_data]
                                    has_result = True
                        except: pass
            conn.commit()
            return {"success": True, "data": final_rows}
        except Exception as e: return {"success": False, "error": str(e), "data": []}
        finally:
            if should_close: conn.close()

    def process_files(self, file_paths: List[str], model_client=None, status_callback=None) -> Dict[str, Any]:
        try:
            print("\n" + "🏗️  [Data Base Construction] 启动知识库物理底座构建..." + "\n" + "="*60)
            if os.path.exists(self.db_path): 
                os.remove(self.db_path)
                print("🧹 [清理] 移除旧数据库文件，准备重新建模")
                
            conn = sqlite3.connect(self.db_path)
            physical_tables = {}
            semantic_docs = []
            
            if status_callback: status_callback(f"📊 正在扫描文件并识别业务蓝图...")
            
            for path in file_paths:
                name = os.path.basename(path).lower()
                if name.endswith(('.md', '.pdf', '.docx', '.txt')):
                    print(f"📄 [识别] 逻辑文档: {name} (待提取 Schema)")
                    semantic_docs.append(path); continue
                    
                t_name = re.sub(r'[^a-zA-Z0-9_]', '_', os.path.splitext(name)[0])
                try:
                    df = pd.read_csv(path) if name.endswith('.csv') else pd.read_excel(path)
                    df.columns = [re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5]', '_', str(c)) for c in df.columns]
                    df.to_sql(t_name, conn, index=False, if_exists='replace')
                    col_count = len(df.columns)
                    row_count = len(df)
                    physical_tables[t_name] = {"cols": [{"name": c, "type": str(t)} for c, t in df.dtypes.items()]}
                    print(f"📊 [固化] 真实数据表: {t_name} | 规模: {col_count}列 x {row_count}行")
                except Exception as e:
                    print(f"❌ [失败] 无法解析数据文件 {name}: {e}")
                    
            conn.close()
            
            modeling_summary = "多维业务分析"
            if model_client and physical_tables:
                print("🧠 [理解] 正在通过 AI 总结物理表之间的业务逻辑关系...")
                modeling_summary = model_client.complete(f"总结业务逻辑: {json.dumps(physical_tables)}").text.strip()
                print(f"📝 [摘要] 业务背景: {modeling_summary[:100]}...")

            unified_schema = {"tables": physical_tables, "macro_context": modeling_summary}
            
            if semantic_docs and model_client:
                print(f"🔍 [建模] 正在从 {len(semantic_docs)} 个逻辑文档中深度提取表结构定义...")
                docs = "".join([open(p, 'r', errors='ignore').read()[:5000] for p in semantic_docs])
                prompt = f"""分析以下文档，提取所有表的结构定义。

文档内容：
{docs}

要求：
1. 识别所有提到的表名
2. 提取每个表的字段定义（字段名、类型、说明）
3. 返回标准 JSON 格式

返回格式：
{{
  "macro_context": "业务背景描述",
  "tables": {{
    "表名": {{
      "desc": "表说明",
      "cols": [
        {{"name": "字段名", "type": "类型", "comment": "说明"}}
      ]
    }}
  }}
}}

只返回 JSON，不要其他内容。"""
                
                try:
                    res = model_client.complete(prompt).text
                    match = re.search(r'(\{.*\})', res, re.DOTALL)
                    if match:
                        semantic = json.loads(match.group(1))
                        extracted_tables = semantic.get('tables', {})
                        if extracted_tables:
                            print(f"✅ [成功] 从文档提取了 {len(extracted_tables)} 个逻辑表结构")
                            for t, info in extracted_tables.items():
                                if t in unified_schema['tables']: 
                                    unified_schema['tables'][t].update(info)
                                    print(f"   • 完善已知表: {t}")
                                else: 
                                    unified_schema['tables'][t] = info
                                    unified_schema['tables'][t]['is_virtual'] = True
                                    print(f"   • 发现新逻辑表: {t} ({len(info.get('cols', []))}个字段)")
                            unified_schema['macro_context'] = semantic.get('macro_context', modeling_summary)
                except Exception as e:
                    print(f"❌ [建模失败] 无法从文档提取 Schema: {e}")
                
            # 保存 Schema
            with open(self.schema_path, 'w', encoding='utf-8') as f: 
                json.dump(unified_schema, f, indent=4, ensure_ascii=False)
            print(f"💾 [固化] 业务蓝图已保存至: {os.path.basename(self.schema_path)}")
            
            # 强制固化底座：如果表是空的，立刻生成仿真数据
            if model_client:
                print("\n" + "🎲 [仿真] 启动“无数造数”流程，填充物理底座...")
                if status_callback: status_callback("🧪 正在固化业务数据底座 (有数治数/无数造数)...")
                self._ensure_sandbox_ready(unified_schema, model_client, status_callback=None)
                
            if status_callback: status_callback(f"✅ 全域建模完成，DB 底座已就绪")
            print("="*60 + "\n" + "✨ [Success] 数据分析物理底座构建完成，business_data.db 已就绪" + "\n")
            return {"success": True, "tables": list(unified_schema['tables'].keys())}
        except Exception as e: return {"success": False, "error": str(e)}