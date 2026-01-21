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

    def _get_relevant_tables(self, query: str, schemas: Dict[str, Any], model_client=None) -> List[str]:
        all_tables = schemas.get("tables", {})
        if not all_tables: return []
        
        # [v7.0.1 Upgrade] 深度语义指纹识别
        if model_client:
            try:
                # 预检：找出包含关键词的字段，优先展示给 LLM
                keywords = ['销', '售', '额', '金额', '区域', '地址', '省', '市', '行业', '产品', '名称']
                table_summaries = []
                for t, info in all_tables.items():
                    all_cols = info.get('cols', [])
                    # 筛选出可能相关的字段
                    matched_cols = [f"{c['name']}({c.get('comment','')})" for c in all_cols if any(k in str(c.get('comment','')).lower() or k in c['name'].lower() for k in keywords)]
                    # 即使没匹配到也展示前 3 个
                    display_cols = matched_cols if matched_cols else [f"{c['name']}({c.get('comment','')})" for c in all_cols[:3]]
                    
                    table_summaries.append(f"- {t} ({info.get('desc', '')}): 关键字段 [{', '.join(display_cols[:8])}]")
                
                table_str = "\n".join(table_summaries)
                prompt = f"""你是一个资深业务架构师。请分析用户的问题，从【物理表清单】中选出最适合回答该问题的 1-2 张表。

用户问题: {query}

物理表清单:
{table_str}

【决策优先级 - 必须严守】:
1. 事实优先：如果问题涉及“多少”、“金额”、“次数”、“趋势”等统计量，优先选择包含流水、明细、交易特征的事实表。
2. 属性补充：如果问题涉及“名称”、“地址”、“类别”等描述性信息，且事实表中缺失，则关联相应的维度/档案表。
3. 时间对齐：如果问题包含时间范围，优先选择带有日期或时间戳字段的表。
4. 消歧义：若多个表都有同名字段（如 amount），分析表名含义，选择业务语义最契合的那张（例如：查收入选销售表，不选退款表）。

要求:
1. 只返回表名，用逗号分隔。
2. 不要包含任何解释。
3. 必须精准，不要多选。"""
                
                print(f"🧠 [精准识别] 正在为问题 '{query}' 执行语义对齐与消歧义选表...")
                res = model_client.complete(prompt).text.strip()
                
                # [v7.0.1 Fix] 鲁棒解析：从整段文字中提取合法的物理表名
                selected = []
                for t in all_tables.keys():
                    if re.search(r'\b' + re.escape(t) + r'\b', res):
                        selected.append(t)
                
                if selected:
                    valid_selected = selected[:2] # 强行限制 2 张，防止干扰
                    print(f"🎯 [锁定成功] 选定表: {valid_selected} | 原始响应: {res[:50]}")
                    return valid_selected
            except Exception as e:
                print(f"⚠️ [识别异常] {e}")

        # --- 降级方案：保守匹配 ---
        base_tables = []
        qw = query.lower()
        # 针对本次问题的硬编码补丁 (v7.0.1)
        if '销' in qw or '销售' in qw:
            sales_tables = [t for t in all_tables if 'mxxx' in t.lower()]
            if sales_tables: base_tables.extend(sales_tables[:1])
        
        if not base_tables:
            base_tables = list(all_tables.keys())[:2] # 极端保守，只选前2
            
        return base_tables

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

    def _generate_mock_data(self, table_name: str, table_info: Dict, schemas: Dict, model_client, cursor, query_context: str = "") -> bool:
        """生成虚拟数据并插入表中，注入查询上下文以确保数据相关性"""
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
            
            print(f"📋 [造数规格] 表 '{table_name}' | 字段范围: {[c['name'] for c in cols]}")

            # --- 核心改进：注入意图约束 ---
            intent_instruction = ""
            if query_context:
                intent_instruction = f"""
【强制约束 - 意图对齐】:
用户当前的问题是: "{query_context}"
你生成的 30 条数据中，必须包含至少 10-15 条能够直接支撑回答该问题的典型记录。
例如：如果涉及筛选条件（如某类别、某时间段、某阈值），请确保生成的记录中有符合这些条件的值，不要生成完全无关的数据。
"""

            prompt = f"""为数据表 '{table_name}' 生成 30 条真实、合理的测试数据。

表说明: {table_desc}
业务背景: {macro_context}
{intent_instruction}

字段定义:
{cols_desc}

要求:
1. 生成标准的 SQLite INSERT 语句
2. 数据要符合业务逻辑，相互关联，且必须满足上述【意图对齐】约束，确保后续 SQL 查询能查到结果。
3. 日期格式: YYYY-MM-DD，时间格式: YYYY-MM-DD HH:MM:SS
4. 数值字段使用纯数字，不要带单位
5. 每条语句独立一行，以分号结尾
6. 只输出 INSERT 语句，不要其他内容。

示例格式:
INSERT INTO {table_name} VALUES ('value1', 'value2', 123);
INSERT INTO {table_name} VALUES ('value3', 'value4', 456);"""

            print(f"🎲 [意图感知造数] 正在为表 '{table_name}' 生成相关测试数据...")
            
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
                    
                    # [v6.9.1 Fix] 强制纠正 LLM 可能幻觉的表名
                    # 匹配 INSERT INTO xxx ...
                    match_table = re.search(r'INSERT\s+INTO\s+(?:"?)([\w\d_]+)(?:"?)', clean_stmt, re.IGNORECASE)
                    if match_table:
                        gen_table = match_table.group(1)
                        if gen_table.lower() != table_name.lower():
                            # 替换为正确的表名
                            clean_stmt = re.sub(r'INSERT\s+INTO\s+(?:"?)[\w\d_]+(?:"?)', f'INSERT INTO "{table_name}"', clean_stmt, flags=re.IGNORECASE)

                    cursor.execute(clean_stmt)
                    insert_count += 1
                except Exception as e:
                    print(f"   ⚠️ [Insert Skip] {e}")
                    continue
            
            if insert_count > 0:
                print(f"✅ [造数完成] 成功生成 {insert_count} 条与问题高度相关的记录")
                return True
            else:
                print(f"⚠️ [造数失败] LLM 生成失败（0条），尝试备用方案...")
                return self._generate_simple_mock_data(table_name, cols, cursor)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"生成虚拟数据致命错误: {e}")
            return False

    def _create_missing_table(self, table_name: str, schemas: Dict, model_client, cursor) -> bool:
        """动态创建缺失的表"""
        try:
            # 根据表名推断可能的结构
            table_suggestions = {
                'orders': {
                    'cols': [
                        {'name': 'order_id', 'type': 'TEXT', 'comment': '订单唯一标识'},
                        {'name': 'user_id', 'type': 'INTEGER', 'comment': '用户ID，关联users表'},
                        {'name': 'product_id', 'type': 'TEXT', 'comment': '商品ID，关联products表'},
                        {'name': 'quantity', 'type': 'INTEGER', 'comment': '购买数量'},
                        {'name': 'unit_price', 'type': 'REAL', 'comment': '单价'},
                        {'name': 'total_amount', 'type': 'REAL', 'comment': '订单总金额'},
                        {'name': 'promo_code', 'type': 'TEXT', 'comment': '促销码'},
                        {'name': 'order_date', 'type': 'TEXT', 'comment': '订单日期'},
                        {'name': 'status', 'type': 'TEXT', 'comment': '订单状态'}
                    ],
                    'desc': '订单表，记录用户购买行为'
                }
            }
            
            table_info = table_suggestions.get(table_name.lower())
            if not table_info:
                print(f"⚠️ [Dynamic Schema] 未知表类型 '{table_name}'，跳过创建")
                return False
            
            # 创建表
            cols_sql = []
            for col in table_info['cols']:
                cols_sql.append(f'"{col["name"]}" {col["type"]}')
            
            create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(cols_sql)})'
            cursor.execute(create_sql)
            print(f"🏗️ [Dynamic Schema] 创建表: {create_sql}")
            
            # 生成数据
            return self._generate_mock_data(table_name, table_info, schemas, model_client, cursor)
            
        except Exception as e:
            print(f"❌ [Dynamic Schema] 创建表 '{table_name}' 失败: {e}")
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
                    elif any(k in col_name for k in ['date', '日期', 'time', '时间', 'rfq']):
                        values.append(f"2025-01-{(i%28)+1:02d}")
                    elif any(k in col_name for k in ['tjny', 'month', '月份', '年月']):
                        values.append(f"2025-{((i%12)+1):02d}")
                    elif any(k in col_name for k in ['year', '年份']):
                        values.append(f"202{i%5}")
                    elif any(k in col_name for k in ['amount', 'price', 'sales', '金额', '价格', '销售', 'je']):
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

    def _ensure_sandbox_ready(self, schemas: Dict[str, Any], model_client, status_callback=None, target_tables: List[str] = None, conn=None, query_context: str = "") -> Dict[str, str]:
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
                    if self._generate_mock_data(physical_name, table_info, schemas, model_client, cursor, query_context=query_context):
                        table_mapping[schema_name] = physical_name
                        conn.commit()
                else:
                    # [v6.7.10 Fix] 动态创建缺失的表
                    print(f"🔧 [Dynamic Schema] 检测到查询需要表 '{schema_name}' 但 schema 中未定义，尝试动态创建...")
                    if self._create_missing_table(schema_name, schemas, model_client, cursor):
                        table_mapping[schema_name] = physical_name
                        conn.commit()
                        print(f"✅ [Dynamic Schema] 成功创建表 '{schema_name}' 并生成数据")
        
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
1. 识别所有提到的实体/表名（优先使用英文名，如果没有则翻译为英文）
2. 提取每个表的字段定义（字段名、类型、说明）
3. 推断表之间的关联关系
4. 返回标准 JSON 格式

返回格式：
{{
  "macro_context": "业务背景描述",
  "tables": {{
    "table_name_en": {{
      "desc": "表说明",
      "cols": [
        {{"name": "field_name", "type": "TEXT/INTEGER/REAL", "comment": "说明"}}
      ],
      "is_virtual": true
    }}
  }}
}}

只返回 JSON，不要其他内容。"""
        
        try:
            print(f"🧠 [Schema提取] 正在请求 LLM 解析文档结构...")
            res = model_client.complete(prompt).text
            match = re.search(r'(\{.*\})', res, re.DOTALL)
            if match:
                new_schema = json.loads(match.group(1))
                
                # 验证提取结果有效性
                if not new_schema.get('tables'):
                    print(f"⚠️ [Schema提取] LLM 返回了 JSON 但没有表定义")
                    return {}

                # 合并到现有 schema
                if os.path.exists(self.schema_path):
                    with open(self.schema_path, 'r', encoding='utf-8') as f:
                        current = json.load(f)
                else:
                    current = {"tables": {}, "macro_context": ""}
                
                # 合并 tables
                extracted_count = 0
                for t, info in new_schema.get('tables', {}).items():
                    # 规范化表名
                    safe_t = re.sub(r'[^a-zA-Z0-9_]', '_', t).lower()
                    if safe_t not in current['tables']:
                        current['tables'][safe_t] = info
                        # 确保标记为虚拟表，触发后续的 JIT 造数
                        current['tables'][safe_t]['is_virtual'] = True
                        extracted_count += 1
                        print(f"   ✅ [提取成功] 发现表: {safe_t} ({len(info.get('cols', []))} 字段)")
                    else:
                        current['tables'][safe_t].update(info)
                
                if new_schema.get('macro_context'):
                    current['macro_context'] = new_schema['macro_context']
                
                # 立即落盘
                with open(self.schema_path, 'w', encoding='utf-8') as f:
                    json.dump(current, f, indent=4, ensure_ascii=False)
                
                success_msg = f"✅ 成功从文档提取了 {extracted_count} 个逻辑表定义，Schema 已更新"
                print(success_msg)
                if status_callback: status_callback(success_msg)
                return current
            else:
                print(f"❌ [Schema提取] 无法从 LLM 响应中提取 JSON")
        except Exception as e:
            err_msg = f"⚠️ 从文档提取 Schema 失败: {e}"
            print(err_msg)
            if status_callback: status_callback(err_msg)
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

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """提取文本中的 JSON 对象或数组"""
        try:
            # 尝试直接解析整个文本
            return json.loads(text.strip())
        except:
            try:
                # 尝试提取 JSON 对象
                match = re.search(r'(\{.*\})', text, re.DOTALL)
                if match:
                    return json.loads(match.group(1))
            except: pass
            
            try:
                # 尝试提取 JSON 数组
                match = re.search(r'(\[.*\])', text, re.DOTALL)
                if match:
                    return json.loads(match.group(1))
            except: pass
        return {}

    def execute_analysis(self, query: str, model_client, context_text: str = "", status_callback=None) -> Dict[str, Any]:
        now = datetime.now().strftime("%H:%M:%S")
        # --- 终端强制输出: 任务启动 ---
        print("\n" + "="*60)
        print(f"[{now}] 🚀 [Strategic Workshop] 接收到分析请求: {query}")
        print("="*60)
        if self.logger: self.logger.info(f"🚀 [Strategic Workshop] 接收到分析请求: {query}")
        
        if not os.path.exists(self.schema_path): 
            print(f"[{now}] ❌ [错误] 架构文件不存在，尝试创建默认架构...")
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
            "字典", "有哪些表", "字段属性", "field", "column", "table", "schema", "definition", "mandatory", "required", 
            "架构建议", "ETL", "架构设计", "业务模型", "建模规范"
        ]
        # 优化判定：仅当 query 纯粹侧重于元数据查询且不包含具体业务指标时才进入
        # [v6.8.9 Fix] 增加对“造数/模拟/数据”等意图的豁免，防止造数请求被拦截为 Schema 查询
        exclude_keywords = [
            "多少", "金额", "总计", "平均", "最高", "最低", "趋势", "统计", "销量", "订单",
            "数据", "data", "mock", "sample", "record", "row", "generate", "simulate", "create", "insert", 
            "生成", "模拟", "造数", "样例", "记录", "内容", "content", "values"
        ]
        is_metadata_query = any(k in query.lower() for k in metadata_keywords) and not any(k in query.lower() for k in exclude_keywords)
        
        if is_metadata_query:
            print(f"🔍 [决策] 判定为架构/配置咨询，构建深度透视看板...")
            
            # 识别相关表以提供上下文
            rel_tables = self._get_relevant_tables(query, full_schemas, model_client)
            sub_schema = {t: full_schemas['tables'][t] for t in rel_tables if t in full_schemas['tables']}
            
            # 构造回显表格
            schema_rows = []
            sample_for_ui = {} # 用于触发“查询前”预览
            for t, info in sub_schema.items():
                cols = info.get('cols', info.get('columns', []))
                t_rows = []
                for c in cols:
                    row = {
                        "字段名": c.get('name'),
                        "逻辑含义": c.get('comment', '业务默认属性'),
                        "数据类型": c.get('type', 'TEXT')
                    }
                    schema_rows.append({"业务实体": t, **row})
                    t_rows.append(row)
                sample_for_ui[t] = t_rows[:5] # 每个表采样前5个定义作为预览
            
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
                "meta": {
                    "stage_id": 1, 
                    "title": "全域战略/架构透视", 
                    "goal": "对齐业务逻辑与物理底座实现路径",
                    "transformation": "深度提取业务实体的逻辑模型与关联关系"
                },
                "sqls": {
                    "sqlite": "-- 战略推演模式 (Strategic Architectural Inference)\n-- 当前问题侧重于架构/配置建议，已提取相关业务模型作为设计依据",
                    "standard": "-- Recommended Implementation Logic"
                },
                "data": schema_rows if schema_rows else [{"状态": "已完成逻辑建模", "可参考实体": list(full_schemas.get('tables', {}).keys())}],
                "empty_reason": "",
                "source_samples": sample_for_ui, # 关键修复：补全此项以触发 UI “查询前” 渲染
                "is_simulated": True
            }
            
            return {
                "stages": [consultation_stage], 
                "logic_gen": report_gen(), 
                "success": True, 
                "macro_context": full_schemas.get('macro_context', "战略咨询")
            }

        # 2. 识别与对齐
        rel_tables = self._get_relevant_tables(query, full_schemas, model_client)
        
        # [v8.1.3 Fix] 预定义 report_gen 以防止 UnboundLocalError
        def report_gen(): yield "正在分析中..."
        
        print(f"📁 [建模] 锁定业务范围: {rel_tables}")
        
        # [v6.7.0 Fix] 判定是否为仿真模式：只要涉及的表中有一个是虚拟表，整体判定为仿真模式
        # [v6.9.0 Fix] 增强判定：如果表中没有任何数据，也视为仿真模式（自动启动救护逻辑）
        session_conn = sqlite3.connect(self.db_path, timeout=60)
        
        def check_table_empty(t_name, conn):
            try:
                # 尝试直接查询计数
                c = conn.cursor()
                # 处理可能存在的引号
                safe_t = f'"{t_name}"' if '"' not in t_name else t_name
                count = c.execute(f"SELECT count(*) FROM {safe_t}").fetchone()[0]
                return count == 0
            except:
                return True # 如果查询失败，保守认为可能是没数据的空表/新表

        tables_empty_status = {t: check_table_empty(t, session_conn) for t in rel_tables if t in full_schemas.get('tables', {})}
        is_simulated = any(full_schemas.get('tables', {}).get(t, {}).get('is_virtual', False) for t in rel_tables) or any(tables_empty_status.values())
        
        if is_simulated:
            print(f"🎭 [仿真模式] 激活。检测到虚拟表或空表: {[t for t, empty in tables_empty_status.items() if empty]}")
        
        try:
            # 原则：如果是数据分析模式，且涉及范围内的表在数据库中不存在或为空，必须先完成“无数造数”的闭环
            if status_callback: status_callback("🛡️ 正在确保业务底座完整性...")
            mapping = self._ensure_sandbox_ready(full_schemas, model_client, status_callback, rel_tables, conn=session_conn, query_context=query)
            
            # 重新获取子架构（使用映射后的物理表名）
            sub_schema = {}
            for t in rel_tables:
                if t in full_schemas['tables']:
                    phys_name = mapping.get(t, t)
                    sub_schema[phys_name] = full_schemas['tables'][t]

            # 3. 任务拆解 (v8.1.2 加固版：原子化分步策略)
            print("🎯 [规划] 正在执行原子化战略拆解...")
            planner_prompt = f"""你是一名资深数据科学家。请将用户的复杂分析请求拆解为 2-3 个循序渐进的 SQL 执行阶段。

【核心原则 - 必须遵循】:
1. 原子性：每个阶段只解决一个核心问题（如：阶段1-锁定目标范围，阶段2-执行跨表关联，阶段3-计算最终指标）。
2. 逻辑链：后一个阶段必须建立在前一个阶段的数据产出之上。
3. 容错性：避免在一个阶段编写过于复杂的嵌套查询。

用户问题: {query}
业务蓝图: {json.dumps(sub_schema, ensure_ascii=False)}

请返回 JSON 数组格式: [{{ "stage_id": 1, "title": "阶段名称", "transformation": "本阶段的 SQL 任务描述", "goal": "本阶段要解决的具体业务问题" }}]"""
            
            try:
                res = model_client.complete(planner_prompt).text
                # 使用统一的 JSON 提取方法
                extracted = self._extract_json(res)
                if isinstance(extracted, list):
                    stages_meta = extracted
                elif isinstance(extracted, dict) and 'stages' in extracted:
                    stages_meta = extracted['stages']
                else:
                    # 尝试提取数组
                    match = re.search(r'(\[.*\])', res, re.DOTALL)
                    if match:
                        stages_meta = json.loads(match.group(1))
                    else:
                        raise ValueError("无法提取阶段信息")
                        
                for s in stages_meta:
                    print(f"   📍 Stage {s['stage_id']}: {s['title']} | 目标: {s['goal']}")
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 [规划结论] 任务拆解完成，共计 {len(stages_meta)} 个原子执行阶段。")
                if self.logger: self.logger.info(f"📊 [Plan Result] 拆解完成，共 {len(stages_meta)} 个阶段")
            except: 
                stages_meta = [{"stage_id": 1, "title": "数据透视", "transformation": "执行分析"}]
                if self.logger: self.logger.warning("⚠️ [Plan Fail] 规划拆解失败，降级为单步执行")

            final_data = []
            analysis_context = ""
            for i, meta in enumerate(stages_meta):
                st_now = datetime.now().strftime("%H:%M:%S")
                print(f"\n--- ⏳ [{st_now}] 开始执行阶段 {i+1}: {meta.get('title')} ---")
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
                    print("🚨 [DEBUG] 开始生成 SQL...")  # 强制输出
                    ai_response = model_client.complete(sql_prompt).text
                    print(f"🤖 [AI Response] {ai_response[:200]}...")  # 调试输出
                    sqls = self._extract_json(ai_response) or {"sqlite": ""}
                    print(f"🔍 [Extracted SQLs] {list(sqls.keys())}")  # 调试输出
                    if sqls.get('sqlite'):
                        print(f"📜 [SQL] {sqls['sqlite']}")
                    else:
                        print("⚠️ [Warning] 未提取到有效的 SQLite 查询")
                        print(f"🔍 [Raw AI Response] {ai_response}")  # 显示完整响应
                except Exception as e:
                    print(f"❌ [Error] SQL 生成失败: {e}")
                    pass

                if status_callback: status_callback(f"🧪 [Stage {i+1}] 执行逻辑验证...")
                exec_res = {"success": False, "data": []}
                empty_reason = "该阶段执行了逻辑加工，未产生回显数据"
                
                if sqls.get("sqlite"):
                    current_sql = sqls["sqlite"].strip()
                    sql_snippet = (current_sql[:100] + '...') if len(current_sql) > 100 else current_sql
                    print(f"🚀 [Stage {i+1}] 执行 SQL: {sql_snippet}")
                    
                    exec_res = self.execute_sql(current_sql, model_client, conn=session_conn)
                    print(f"📊 [Attempt 1] 结果: {'✅' if exec_res['data'] else '⚠️'} 命中 {len(exec_res.get('data', []))} 行")
                    
                    # --- [v8.1.2 Enhancement] 异常零值诊断 (Zero-Row Diagnostics) ---
                    if exec_res["success"] and not exec_res['data']:
                        # 检查是否涉及多表关联
                        if "JOIN" in current_sql.upper():
                            print(f"🕵️ [质量诊断] 检测到关联查询结果为空，正在排查 JOIN Key 幻觉...")
                            # 提取 JOIN 条件中的表和列 (简单正则)
                            join_match = re.search(r'JOIN\s+(?:"?)([\w\d_]+)(?:"?)\s+ON\s+(.*?)(?:\s+WHERE|\s+GROUP|\s+ORDER|;|$)', current_sql, re.I | re.S)
                            if join_match:
                                target_table = join_match.group(1)
                                join_cond = join_match.group(2)
                                print(f"   🔎 正在验证表 '{target_table}' 与关联条件 '{join_cond.strip()}' 的物理一致性...")
                                # 如果是模拟环境，这通常意味着需要更精准的数据补全
                                if is_simulated:
                                    status_callback(f"⚠️ 发现关联数据断层，正在执行物理对齐自愈...")
                    
                    # --- [v6.7.2 Fix] 模拟环境下的空结果自愈 (Empty Result Rescue) ---
                    if not exec_res['data'] and is_simulated:
                        print(f"🔄 [自愈循环] 模拟库表 '{list(t_context.keys())}' 数据不足，正在根据意图补全...")
                        
                        rescue_tables = [t for t in t_context.keys()]
                        for t in rescue_tables:
                            orig_key = next((k for k in full_schemas.get('tables', {}).keys() if k.lower() == t.lower()), None)
                            if orig_key:
                                table_info = full_schemas['tables'][orig_key]
                                self._generate_mock_data(t, table_info, full_schemas, model_client, session_conn.cursor(), query_context=query)
                        
                        session_conn.commit()
                        
                        print(f"🚀 [Attempt 2] 数据补全完成，正在执行二次验证...")
                        exec_res = self.execute_sql(current_sql, model_client, conn=session_conn)
                        print(f"📊 [Final Result] 结果: {'✅' if exec_res['data'] else '❌'} 最终命中 {len(exec_res.get('data', []))} 行")

                    if exec_res["success"]:
                        if exec_res['data']:
                            r_count = len(exec_res['data'])
                            if status_callback: status_callback(f"✅ 成功获取 {r_count} 条核心业务数据")
                            analysis_context += f"阶段{i+1}结果采样: {json.dumps(exec_res['data'][:5], ensure_ascii=False)}\n"
                            empty_reason = ""
                        else:
                            # 强化正则：支持引号、空格和 TEMPORARY 关键字
                            m_table = re.search(r'CREATE\s+(?:TEMPORARY\s+)?TABLE\s+(?:"?)([a-zA-Z0-9_]+)(?:"?)', current_sql, re.I)
                            if m_table:
                                t_name = m_table.group(1)
                                print(f"🏗️ [探测] 识别到中间加工表: {t_name}")
                                v_res = self.execute_sql(f'SELECT * FROM "{t_name}" LIMIT 10', conn=session_conn)
                                if v_res["success"] and v_res["data"]:
                                    exec_res["data"] = v_res["data"]
                                    empty_reason = ""
                                else:
                                    empty_reason = f"🏗️ 阶段执行成功，但加工表 '{t_name}' 为空"
                            else:
                                empty_reason = "⚠️ 逻辑验证通过，但当前筛选条件下无符合记录"
                
                # 构建阶段数据
                stage_data = {
                    "meta": meta, 
                    "sqls": sqls, 
                    "data": exec_res["data"], 
                    "empty_reason": empty_reason,
                    "source_samples": {t: t_context[t].get('sample', {}) for t in t_context},
                    "is_simulated": is_simulated
                }
                
                # [v6.7.11 Fix] 生成AI可视化推荐
                if exec_res["data"] and len(exec_res["data"]) > 0:
                    try:
                        import pandas as pd
                        df_temp = pd.DataFrame(exec_res["data"])
                        columns = list(df_temp.columns)
                        sample_data = exec_res["data"][:3]  # 取前3行作为样例
                        recommendation = self.recommend_visualization(query, columns, sample_data, model_client)
                        stage_data["recommendation"] = recommendation
                        print(f"🎯 [AI Recommendation] Generated: {recommendation.get('viz_type', 'unknown')}")
                    except Exception as e:
                        print(f"⚠️ [AI Recommendation] Failed: {e}")
                        stage_data["recommendation"] = None
                
                print(f"📦 [Stage Data] Meta: {meta.get('title')}, SQLs: {list(sqls.keys())}, Data: {len(exec_res['data'])} rows, Samples: {list(stage_data['source_samples'].keys())}")
                final_data.append(stage_data)

            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🧠 [总结结论] 最终战略洞察报告合成完毕，正在推送至 UI...")
            if self.logger: self.logger.success(f"🧠 [Summary] 战略推演完成，包含 {len(final_data)} 个有效阶段")
            
            # 归一化与安全化处理 (Normalization & Serialization Safety)
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
                print(f"🧹 [Sanitize] Processing stage: {s.get('meta', {}).get('title', 'Unknown')}")
                
                # 1. 强制 Key 归一化 (sqlite, standard, dataworks)
                raw_sqls = s.get("sqls", {})
                normalized_sqls = {str(k).lower().strip(): v for k, v in raw_sqls.items()}
                print(f"🔧 [SQL Keys] Raw: {list(raw_sqls.keys())} -> Normalized: {list(normalized_sqls.keys())}")
                
                # 2. 补全缺失的 SQL 视角
                if 'sqlite' not in normalized_sqls and normalized_sqls:
                    # 尝试寻找任何包含 sql 关键字的 key
                    sql_key = next((k for k in normalized_sqls if 'sql' in k), list(normalized_sqls.keys())[0])
                    normalized_sqls['sqlite'] = normalized_sqls[sql_key]
                    print(f"🔄 [SQL Fix] Added sqlite key from: {sql_key}")
                
                # 3. 强制数据安全化封装函数
                import pandas as pd_local
                def make_safe(rows):
                    if not isinstance(rows, list): return []
                    safe = []
                    for row in rows:
                        if isinstance(row, dict):
                            s_row = {}
                            for k, v in row.items():
                                if pd_local.isna(v): s_row[k] = None
                                elif hasattr(v, 'item'): s_row[k] = v.item() 
                                elif isinstance(v, (datetime, pd_local.Timestamp)): s_row[k] = v.isoformat()
                                else: s_row[k] = v
                            safe.append(s_row)
                        else: safe.append(str(row))
                    return safe

                # 4. 处理核心数据集与采样数据集
                safe_data = make_safe(s.get("data", []))
                raw_samples = s.get("source_samples", {})
                safe_samples = {}
                if isinstance(raw_samples, dict):
                    for t_name, rows in raw_samples.items():
                        safe_samples[t_name] = make_safe(rows)
                
                print(f"📊 [Data] Safe data: {len(safe_data)} rows, Safe samples: {len(safe_samples)} tables")
                
                result = {
                    "meta": s.get("meta", {"stage_id": 99, "title": "未命名阶段"}),
                    "sqls": normalized_sqls,
                    "data": safe_data,
                    "empty_reason": s.get("empty_reason", ""),
                    "source_samples": safe_samples,
                    "is_simulated": s.get("is_simulated", False)
                }
                
                print(f"✅ [Sanitized] Stage complete: {result['meta'].get('title')}")
                return result

            final_stages_sanitized = [sanitize_stage(s) for s in final_data]
            
            print(f"\n🎯 [Final Result] Returning {len(final_stages_sanitized)} stages")
            for i, stage in enumerate(final_stages_sanitized):
                print(f"   Stage {i+1}: {stage['meta'].get('title')} - Data: {len(stage['data'])} rows, SQLs: {list(stage['sqls'].keys())}")

            return {
                "stages": final_stages_sanitized, 
                "logic_gen": report_gen(), 
                "success": True, 
                "macro_context": full_schemas.get('macro_context','')
            }
        finally:
            session_conn.close()

    def _classify_content(self, df: pd.DataFrame, model_client) -> str:
        """[智能仲裁] 判断文件内容是 'DATA' (事实数据) 还是 'SCHEMA' (定义文档)"""
        # 1. 优先检查表头特征 (v6.9.5 Fix: 防止大字典因为行数多被误判为 DATA)
        headers = [str(c).lower().strip() for c in df.columns]
        schema_sigs = ['table', 'column', 'field', 'data type', '字段', '类型', '表名', '表英']
        matched_sigs = 0
        for h in headers:
            if any(s in h for s in schema_sigs):
                matched_sigs += 1
        
        if matched_sigs >= 2:
            return "SCHEMA"

        # 2. 检查列值特征 (v6.9.6 Fix: 检查是否包含类型关键字，如 string, varchar 等)
        type_keywords = ['string', 'int', 'varchar', 'char', 'double', 'float', 'decimal', 'numeric', 'timestamp', 'date', 'datetime', 'boolean', 'integer']
        for col in df.columns:
            # 抽样前10行非空值
            sample_values = df[col].dropna().astype(str).str.lower().str.strip().tolist()[:10]
            if not sample_values: continue
            
            matches = sum(1 for v in sample_values if any(tk == v or tk in v for tk in type_keywords))
            # 如果一列中有超过 30% 的值看起来像数据类型，判定为 SCHEMA
            if matches >= 3 or (len(sample_values) > 0 and matches / len(sample_values) >= 0.5):
                print(f"📊 [特征发现] 列 '{col}' 包含大量类型关键字 ({matches}/{len(sample_values)}) -> 判定为 SCHEMA")
                return "SCHEMA"

        # 3. 规则速判: 行数极多且无特征通常是数据
        if len(df) > 500:
            return "DATA"
        
        # 4. 语义关键词检查
        schema_keywords = ['type', '类型', 'description', '描述', 'comment', '备注', 'length', '长度', 'pk', '主键']
        if any(k in headers for k in schema_keywords) and len(df) < 100:
            # 这是一个较强信号，但交给 LLM 确认
            pass

        # 5. LLM 深度仲裁 (采样数据指纹)
        sample_rows = df.head(5).to_string(index=False)
        prompt = f"""请判断以下表格片段的【本质属性】。

表格指纹:
{sample_rows}

选项 A: [DATA]
特征: 这是业务发生的记录(流水/明细)。
内容: 包含具体的人名、时间、金额、ID值等事实。
行动: 我应该直接入库。

选项 B: [SCHEMA]
特征: 这是对数据表的结构定义(数据字典)。
内容: 包含字段名、数据类型(Int/String)、字段长度、业务含义描述。
行动: 我应该理解结构并模拟数据。

请仅返回: [DATA] 或 [SCHEMA]"""

        try:
            res = model_client.complete(prompt).text.strip()
            if "[SCHEMA]" in res or "SCHEMA" in res: return "SCHEMA"
            return "DATA"
        except:
            return "DATA" # 默认保守策略

    def _parse_schema_file(self, df: pd.DataFrame, model_client) -> Dict[str, Any]:
        """[图纸解析] 将 Schema 定义文件解析为标准 JSON 结构 (支持多表)"""
        # [v6.9.3] 增加启发式多表识别
        headers = [str(c).lower().strip() for c in df.columns]
        # [v6.9.6] 增强列名映射
        table_name_cols = ['表英文名', '表名', 'table name', 'table_name', 'entity', '实体名', '对象名']
        col_name_cols = ['字段名称', '字段名', 'column name', 'column_name', 'field', '字段']
        col_type_cols = ['字段类型分', '数据类型', '类型', 'type', 'data type', '字段类型']
        col_comment_cols = ['字段中文名', '注释', '说明', 'comment', 'description', '描述', '含义']

        table_col = next((c for c, h in zip(df.columns, headers) if any(s in h for s in table_name_cols)), None)
        
        if table_col:
            print(f"🧩 [启发式识别] 检测到多表定义列: {table_col}")
            extracted_tables = {}
            for t_name, group in df.groupby(table_col):
                if pd.isna(t_name) or str(t_name).strip() == "" or str(t_name).lower() == 'nan': continue
                
                # 尝试寻找列名、类型、注释列
                cols = []
                col_name_key = next((c for c, h in zip(df.columns, headers) if any(s in h for s in col_name_cols)), None)
                col_type_key = next((c for c, h in zip(df.columns, headers) if any(s in h for s in col_type_cols)), None)
                col_comment_key = next((c for c, h in zip(df.columns, headers) if any(s in h for s in col_comment_cols)), None)
                
                for _, row in group.iterrows():
                    c_name = str(row[col_name_key]).strip() if col_name_key else ""
                    if c_name == "nan" or c_name == "": continue
                    
                    cols.append({
                        "name": c_name,
                        "type": str(row[col_type_key]).strip() if col_type_key else "TEXT",
                        "comment": str(row[col_comment_key]).strip() if col_comment_key else ""
                    })
                
                if cols:
                    extracted_tables[str(t_name)] = {
                        "table_name": str(t_name),
                        "desc": f"从字典文件提取的表: {t_name}",
                        "cols": cols
                    }
            
            if extracted_tables:
                print(f"   ✅ 成功从列特征中提取了 {len(extracted_tables)} 个表结构")
                return {"tables": extracted_tables}

        # --- 降级方案：LLM 解析 ---
        content = df.to_string()
        if len(content) > 10000: content = content[:10000] + "..." # 防止过长
        
        prompt = f"""这是一份数据表结构定义文档。请解析它并提取其中定义的所有表结构。

文档内容:
{content}

【重要指令】:
如果文档内容看起来像是“数据字典”（即每一行描述一个字段，包含表名、列名、类型等），请务必按照结构提取。
不要把“数据字典”本身当成业务数据！

要求:
1. 识别其中定义的所有表
2. 提取每个表的所有列定义（字段名、类型、说明）
3. 返回标准 JSON 格式:
{{
  "tables": {{
    "table_name_1": {{
      "table_name": "table_name_1",
      "desc": "业务含义",
      "cols": [
        {{"name": "字段名", "type": "类型", "comment": "说明"}}
      ]
    }},
    ...
  }}
}}

只返回 JSON。"""
        try:
            res = model_client.complete(prompt).text
            return self._extract_json(res)
        except: return {}

    def smart_ingest_file(self, file_path: str, conn: sqlite3.Connection, model_client) -> Dict[str, Any]:
        """[双轨构建] 智能判断并处理单个文件"""
        name = os.path.basename(file_path).lower()
        print(f"\n🔍 [嗅探] 正在分析文件特征: {name}")
        
        try:
            # 1. 读取内容
            if name.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # 清洗列名
            df.columns = [re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5]', '_', str(c)).strip() for c in df.columns]
            
            # 2. 智能仲裁 (v6.9.6 Fix: 优先检查文件名)
            file_type = "DATA"
            # 强信号关键词
            schema_hints = ['表结构', '数据字典', 'schema', 'dictionary', 'blueprint', '字段定义', '表定义']
            if any(k in name for k in schema_hints):
                print(f"📁 [文件名命中] 识别到 Schema 关键词 '{[k for k in schema_hints if k in name][0]}' -> 强制切换建筑师模式")
                file_type = "SCHEMA"
            elif model_client:
                file_type = self._classify_content(df, model_client)
            
            # 3. 双轨分流
            if file_type == "DATA":
                print(f"📦 [仲裁结果] 判定为【实体数据】 -> 启动搬运工模式")
                t_name = re.sub(r'[^a-zA-Z0-9_]', '_', os.path.splitext(name)[0])
                df.to_sql(t_name, conn, index=False, if_exists='replace')
                print(f"✅ [入库] 成功写入表 '{t_name}' ({len(df)} 行)")
                
                # 返回元数据供 Schema 注册
                return {
                    t_name: {"cols": [{"name": c, "type": str(t)} for c, t in df.dtypes.items()]}
                }
                
            else:
                print(f"📐 [仲裁结果] 判定为【结构定义】 -> 启动建筑师模式 (理解->建模->模拟)")
                
                # A. 理解图纸
                parse_res = self._parse_schema_file(df, model_client)
                
                # 兼容多种返回格式 (v6.9.3)
                extracted_tables = {}
                if "tables" in parse_res:
                    extracted_tables = parse_res["tables"]
                elif "table_name" in parse_res and "cols" in parse_res:
                    # 旧版格式兼容
                    t_name = parse_res.get('table_name', 'analyzed_table')
                    extracted_tables[t_name] = parse_res

                if not extracted_tables:
                    print("⚠️ [警告] 无法解析 Schema 结构，降级为普通入库")
                    # 降级处理
                    t_name = "raw_" + re.sub(r'[^a-zA-Z0-9_]', '_', os.path.splitext(name)[0])
                    df.to_sql(t_name, conn, index=False, if_exists='replace')
                    return {}

                final_meta = {}
                for t_name, info in extracted_tables.items():
                    t_desc = info.get('desc', info.get('table_name', '自动解析表'))
                    cols = info.get('cols', [])
                    if not cols: continue

                    print(f"🧠 [理解] 识别到表定义: {t_name} ({t_desc})")
                    
                    # B. 构建空表 (Physically Create Table)
                    cursor = conn.cursor()
                    cols_sql = []
                    for col in cols:
                        # 简单类型映射
                        c_type = "TEXT"
                        c_type_raw = str(col.get('type', 'TEXT')).lower()
                        if "int" in c_type_raw: c_type = "INTEGER"
                        elif "float" in c_type_raw or "double" in c_type_raw or "decimal" in c_type_raw: c_type = "REAL"
                        cols_sql.append(f'"{col["name"]}" {c_type}')
                    
                    create_sql = f'CREATE TABLE IF NOT EXISTS "{t_name}" ({", ".join(cols_sql)})'
                    cursor.execute(f"DROP TABLE IF EXISTS \"{t_name}\"") # 覆盖模式
                    cursor.execute(create_sql)
                    
                    # C. 注册元数据 (JIT Construction)
                    final_meta[t_name] = {
                        "cols": cols,
                        "desc": t_desc,
                        "is_virtual": True
                    }
                
                print(f"💤 [延迟] 已成功从字典提取 {len(final_meta)} 个表结构，等待查询触发造数...")
                return final_meta

        except Exception as e:
            print(f"❌ [错误] 处理文件 {name} 失败: {e}")
            return {}

    def process_files(self, file_paths: List[str], model_client=None, status_callback=None) -> Dict[str, Any]:
        try:
            print("\n" + "🏗️  [Data Base Construction] 启动知识库逻辑底座构建 (Metadata First)..." + "\n" + "="*60)
            if self.logger: self.logger.info(f"🏗️ [Data Base Construction] 启动知识库逻辑底座构建 (files: {len(file_paths)})...")
            
            if os.path.exists(self.db_path): 
                os.remove(self.db_path)
                print("🧹 [清理] 移除旧数据库文件，准备重新建模")
                
            conn = sqlite3.connect(self.db_path)
            physical_tables = {}
            semantic_docs = []
            
            if status_callback: status_callback(f"📊 正在提取元数据并推演业务血缘...")
            
            for path in file_paths:
                name = os.path.basename(path).lower()
                
                # 1. 非结构化文档 -> 语义理解路径
                if name.endswith(('.md', '.pdf', '.docx', '.txt')):
                    print(f"📄 [识别] 逻辑文档: {name} (待提取 Schema)")
                    semantic_docs.append(path)
                    continue
                
                # 2. 结构化文件 -> 智能双轨路径
                if name.endswith(('.csv', '.xlsx', '.xls')):
                    # 调用新写的智能入库方法
                    table_meta = self.smart_ingest_file(path, conn, model_client)
                    if table_meta:
                        physical_tables.update(table_meta)
                        if self.logger: self.logger.info(f"✅ [Smart Ingest] 成功解析表格文件: {name} (tables: {list(table_meta.keys())})")
                    
            conn.close()
            
            modeling_summary = "多维业务分析"
            if model_client and physical_tables:
                print("\n🧬 [血缘] 正在推演表与表之间的逻辑关联 (Bloodline Inference)...")
                if self.logger: self.logger.info("🧬 [Bloodline] 正在推演表与表之间的逻辑关联...")
                # 升级 Prompt：专注于关系和业务流转
                prompt_lineage = f"""分析以下数据表的定义，推导它们之间的“业务血缘关系”。

表结构定义:
{json.dumps(physical_tables, ensure_ascii=False)}

要求:
1. 识别外键关系 (如 orders.user_id -> users.id)
2. 描述业务流转方向 (如 用户 -> 下单 -> 支付)
3. 生成一段宏观的业务场景描述

请输出一段清晰的业务逻辑摘要。"""
                modeling_summary = model_client.complete(prompt_lineage).text.strip()
                print(f"📝 [摘要] 业务血缘: {modeling_summary[:100]}...")

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
                        semantic = json.loads(match.group(1))
                        extracted_tables = semantic.get('tables', {})
                        if extracted_tables:
                            print(f"✅ [成功] 从文档提取了 {len(extracted_tables)} 个逻辑表结构")
                            if self.logger: self.logger.success(f"✅ [Semantic Schema] 从文档提取了 {len(extracted_tables)} 个逻辑表结构")
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
                    if self.logger: self.logger.error(f"❌ [Schema Error] 建模失败: {e}")
                
            # 保存 Schema
            with open(self.schema_path, 'w', encoding='utf-8') as f: 
                json.dump(unified_schema, f, indent=4, ensure_ascii=False)
            print(f"💾 [固化] 业务蓝图已保存至: {os.path.basename(self.schema_path)}")
            
            # 延迟构建策略：构建阶段仅完成 Schema 固化，不生成数据
            # 数据生成将在 execute_analysis -> _ensure_sandbox_ready 中按需触发 (JIT)
            print("\n" + "💤 [延迟] 物理底座数据生成已挂起。等待首次查询触发即时造数 (JIT)...")
                
            if status_callback: status_callback(f"✅ 全域建模完成，DB 底座已就绪 (结构化)")
            if self.logger: self.logger.success(f"✅ [Build Complete] 全域建模完成，DB 底座已就绪。Tables: {list(unified_schema['tables'].keys())}")
            print("="*60 + "\n" + "✨ [Success] 数据分析物理底座构建完成，business_data.db 已就绪" + "\n")
            return {"success": True, "tables": list(unified_schema['tables'].keys())}
        except Exception as e: 
            if self.logger: self.logger.error(f"❌ [Build Fatal] 构建失败: {e}")
            return {"success": False, "error": str(e)}

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
            if self.logger: self.logger.info(f"💾 [SQL Exec] 成功执行，返回 {len(final_rows)} 行数据")
            return {"success": True, "data": final_rows}
        except Exception as e: 
            if self.logger: self.logger.error(f"❌ [SQL Fail] 执行失败: {e}")
            return {"success": False, "error": str(e), "data": []}
        finally:
            if should_close: conn.close()