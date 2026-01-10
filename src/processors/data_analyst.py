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
        [核心升级] 语义化提取：从自然语言文档（PDF/Word）中识别表结构、数据字典。
        """
        # 合并所有文档的文本片段进行分析
        all_text = "\n".join([d.text for d in docs[:20]]) # 取前20个片段防止Token溢出
        
        prompt = f"""
你是一名顶级的数据库架构师。请从以下文档内容中提取出所有的数据库表结构、字段说明、数据字典及表间关联关系：
{all_text}

请输出一个标准的 JSON 对象，格式如下：
{{
  "tables": {{
    "表名": {{
      "description": "业务含义",
      "columns": [
        {{"name": "字段名", "type": "类型", "comment": "业务解释", "is_primary": true/false}}
      ],
      "foreign_keys": [
        {{"column": "本表字段", "ref_table": "关联表", "ref_column": "关联字段"}}
      ]
    }}
  }}
}}
请仅输出 JSON。
"""
        response = model_client.complete(prompt)
        try:
            schema_data = json.loads(response.text.strip().replace("```json", "").replace("```", ""))
            with open(self.schema_path, 'w', encoding='utf-8') as f:
                json.dump(schema_data, f, indent=4, ensure_ascii=False)
            return schema_data
        except:
            return {"error": "语义解析失败"}

    def infer_business_blueprint(self, schemas: Any, model_client) -> Dict[str, Any]:
        """
        业务推演：推导出业务场景、关联路径和分析建议。
        """
        try:
            # 1. 安全序列化 schemas (防止 unhashable type 等错误)
            if isinstance(schemas, str):
                schemas_str = schemas
            else:
                # 使用 default=str 处理无法序列化的对象
                schemas_str = json.dumps(schemas, indent=2, ensure_ascii=False, default=str)
            
            prompt = f"""
请根据以下数据库结构推导业务全景图：
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
            if self.logger:
                self.logger.error(f"业务推演失败: {e}")
            # 返回兜底数据，防止下游崩溃
            return {
                "business_scenario": "自动推演失败",
                "core_logic": "无法识别",
                "analysis_dimensions": ["通用分析"],
                "error": str(e)
            }

    def execute_analysis(self, query: str, model_client) -> Dict[str, Any]:
        """
        [主动分析版] 强制执行 SQL 并返回结构化结果
        """
        if not os.path.exists(self.schema_path):
             return {"success": False, "logic": "未找到数据结构定义，请先上传数据或文档。"}

        with open(self.schema_path, 'r', encoding='utf-8') as f:
            schemas = json.load(f)
        
        # 获取当前时间，辅助 SQL 生成
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # 1. 强制生成 SQL
        sql_prompt = f"""
你是一名资深 SQLite 专家。基于以下表结构，请生成一条 SQL 来回答用户的问题。
当前日期: {current_date}

表结构：{json.dumps(schemas, ensure_ascii=False)}

用户问题：{query}

要求：
1. 必须返回 SQL，不要反问用户。
2. SQL 必须包裹在 [SQL_START] 和 [SQL_END] 之间。
3. 如果需要计算总额，请使用 SUM()；如果需要计数，请使用 COUNT()。
4. 使用 SQLite 语法。
5. **重要**：如果用户查询"最近"、"上周"等时间范围，请优先基于表中的数据时间分布生成查询（例如：如果数据都是2024年的，不要只查2026年）。可以先查询 MAX(date) 作为参考锚点。
6. 如果问题涉及表中不存在的字段（如单价），请尝试用现有字段计算（如 总额/数量）或仅查询现有字段。
"""
        try:
            # 兼容不同类型的 model_client
            if hasattr(model_client, 'complete'):
                sql_res = model_client.complete(sql_prompt).text
            else:
                # ChatClient 适配
                msgs = [{"role": "user", "content": sql_prompt}]
                sql_res = model_client.chat(model=model_client.model, messages=msgs).message.content
        except Exception as e:
            return {"success": False, "logic": f"模型调用失败: {e}"}

        sql_query = ""
        if "[SQL_START]" in sql_res:
            sql_query = sql_res.split("[SQL_START]")[1].split("[SQL_END]")[0].strip()
        elif "SELECT" in sql_res.upper():
             # Fallback regex
             import re
             match = re.search(r'```sql\s*(.*?)\s*```', sql_res, re.DOTALL | re.IGNORECASE)
             if match:
                 sql_query = match.group(1).strip()
             else:
                 # 尝试直接提取 Select 开头
                 lines = sql_res.split('\n')
                 for line in lines:
                     if line.strip().upper().startswith('SELECT'):
                         sql_query = line.strip()
                         break
        
        # 2. 尝试执行
        execution_result = {"success": False, "data": []}
        if sql_query:
            execution_result = self.execute_sql(sql_query)
        else:
            # 如果没生成 SQL，可能是不需要查库的闲聊
            return {"success": False, "logic": sql_res, "sql": ""}
        
        # 3. 最终业务解读
        summary_prompt = f"""
根据以下 SQL 执行结果，请为用户提供一份简洁的业务分析报告：
SQL: {sql_query}
结果数据: {json.dumps(execution_result.get('data', [])[:20], ensure_ascii=False, default=str)}
问题: {query}

报告结构：
- [💡 逻辑推演]：说明查询了哪些表及字段。
- [📊 核心发现]：用一句话总结数据发现。
- [📈 仿真建议]：说明后续可以关注的业务指标。
"""
        try:
            if hasattr(model_client, 'complete'):
                final_report = model_client.complete(summary_prompt).text
            else:
                msgs = [{"role": "user", "content": summary_prompt}]
                final_report = model_client.chat(model=model_client.model, messages=msgs).message.content
        except:
            final_report = "无法生成分析报告"
        
        return {
            "sql": sql_query,
            "data": execution_result.get('data', []),
            "logic": final_report,
            "success": execution_result.get('success', False)
        }

    def execute_sql(self, sql: str) -> Dict[str, Any]:
        """执行 SQL 并返回字典列表"""
        try:
            conn = sqlite3.connect(self.db_path)
            # 配置 row_factory 以返回字典
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
        """
        物理文件入库：读取 CSV/Excel 并构建 SQLite 数据库
        """
        import re
        try:
            # 重置数据库
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
            
            conn = sqlite3.connect(self.db_path)
            processed_tables = {}
            
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                # 清洗表名: 只保留字母数字和中文
                table_name = os.path.splitext(file_name)[0]
                table_name = re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5]', '_', table_name)
                
                # 读取数据
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                elif file_path.endswith(('.xls', '.xlsx')):
                    df = pd.read_excel(file_path)
                else:
                    continue
                
                # 清洗列名
                df.columns = [re.sub(r'[^a-zA-Z0-9_\u4e00-\u9fa5]', '_', str(c)) for c in df.columns]
                
                # 入库
                df.to_sql(table_name, conn, index=False, if_exists='replace')
                
                # 记录 Schema (用于后续分析)
                processed_tables[table_name] = {
                    "description": f"数据来源: {file_name}",
                    "columns": [{"name": c, "type": str(t)} for c, t in df.dtypes.items()]
                }
            
            conn.close()
            
            # 保存基础 Schema
            with open(self.schema_path, 'w', encoding='utf-8') as f:
                json.dump({"tables": processed_tables}, f, indent=4, ensure_ascii=False)
                
            return {"success": True, "tables": list(processed_tables.keys())}
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"文件处理入库失败: {e}")
            return {"success": False, "error": str(e)}