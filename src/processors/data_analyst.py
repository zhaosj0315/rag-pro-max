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

    def execute_analysis(self, query: str, model_client, context_text: str = "") -> Dict[str, Any]:
        """
        [主动分析版] 强制执行 SQL 并返回结构化结果
        支持语义仿真：如果物理数据库不可用，则利用上下文进行模拟计算
        """
        if not os.path.exists(self.schema_path):
             return {"success": False, "logic": "未找到数据结构定义，请先上传数据或文档。"}

        with open(self.schema_path, 'r', encoding='utf-8') as f:
            schemas = json.load(f)
        
        from datetime import datetime
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # 1. 强制生成 SQL
        sql_prompt = f"""
你是一名资深 SQLite 专家。基于以下表结构，请生成一条 SQL 来回答用户的问题。
当前日期: {current_date}
表结构：{json.dumps(schemas, ensure_ascii=False)}
用户问题：{query}

要求：
1. 必须返回 SQL，包裹在 [SQL_START] 和 [SQL_END] 之间。
2. 尽量使用聚合函数 (SUM, COUNT, AVG) 来回答统计类问题。
3. 如果是多表查询，请使用 JOIN。
4. 仅输出一条 SQL。
"""
        sql_query = ""
        try:
            res = model_client.complete(sql_prompt).text if hasattr(model_client, 'complete') else model_client.chat(model=model_client.model, messages=[{"role":"user","content":sql_prompt}]).message.content
            if "[SQL_START]" in res:
                sql_query = res.split("[SQL_START]")[1].split("[SQL_END]")[0].strip()
            elif "SELECT" in res.upper():
                import re
                match = re.search(r'```sql\s*(.*?)\s*```', res, re.DOTALL | re.IGNORECASE)
                if match:
                    sql_query = match.group(1).strip()
        except: pass

        # 2. 执行与仿真
        execution_result = {"success": False, "data": []}
        is_simulated = False
        
        if sql_query:
            execution_result = self.execute_sql(sql_query)
            
            # 如果执行失败且有上下文，启动仿真
            if not execution_result["success"] and context_text:
                is_simulated = True
                sim_prompt = f"""
你是一名数据分析师。数据库暂时无法访问，请根据提供的【参考数据】和【SQL指令】，模拟计算出查询结果。
SQL: {sql_query}
参考数据: {context_text[:3000]}
请仅输出一个 JSON 数组，例如: [{"列1": "值1", "列2": 100}]
"""
                try:
                    sim_res = model_client.complete(sim_prompt).text if hasattr(model_client, 'complete') else model_client.chat(model=model_client.model, messages=[{"role":"user","content":sim_prompt}]).message.content
                    import re
                    json_match = re.search(r'(\[.*\])', sim_res, re.DOTALL)
                    if json_match:
                        execution_result = {"success": True, "data": json.loads(json_match.group(1))}
                except: pass

        if not execution_result["success"] or not sql_query:
            return {"success": False, "logic": "分析引擎未能获取有效数据", "sql": sql_query}

        # 3. 最终业务解读 (v3.5.1 标准格式)
        summary_prompt = f"""
你是一名资深商业分析师。请根据以下 SQL 和查询结果，撰写一份专业的分析报告。
问题: {query}
SQL: {sql_query}
数据: {json.dumps(execution_result['data'][:15], ensure_ascii=False)}
{"(注意：这是基于上下文仿真的数据)" if is_simulated else ""}

报告必须包含以下模块：
### 💡 核心结论
(一句话总结核心数据发现)

### 📊 数据洞察
(详细解读数据背后的业务逻辑，至少2点)

### 🚀 行动建议
(基于数据给出的具体业务改进建议)
"""
        try:
            final_report = model_client.complete(summary_prompt).text if hasattr(model_client, 'complete') else model_client.chat(model=model_client.model, messages=[{"role":"user","content":summary_prompt}]).message.content
        except: final_report = "分析报告生成失败"
        
        return {
            "sql": sql_query,
            "data": execution_result['data'],
            "logic": final_report,
            "success": True,
            "is_simulated": is_simulated
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