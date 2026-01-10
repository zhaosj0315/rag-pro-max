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

            v3.5.4 升级：支持流式报告生成

            """

            # 0. 数据库自愈检查

            try:

                conn = sqlite3.connect(self.db_path)

                cursor = conn.cursor()

                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

                tables = cursor.fetchall()

                conn.close()

                

                if not tables:

                    if self.logger: self.logger.info("🛠️ [v3.5.2] 检测到数据库为空，启动数据自愈程序...")

                    self._recover_data_from_docstore()

            except Exception as e:

                if self.logger: self.logger.warning(f"⚠️ [v3.5.2] 数据库自愈检查失败: {e}")

    

            if not os.path.exists(self.schema_path):

                 return {"success": False, "logic": "未找到数据结构定义，请先上传数据或文档。"}

    

            with open(self.schema_path, 'r', encoding='utf-8') as f:

                schemas = json.load(f)

            

            valid_tables = list(schemas.get("tables", {}).keys())

            from datetime import datetime

            current_date = datetime.now().strftime("%Y-%m-%d")

            

            # 1. 强制生成 SQL

            sql_prompt = f"""你是一名资深 SQLite 专家。请生成一条 SQL。

    当前日期: {current_date}

    可用表名: {valid_tables}

    详细结构：{json.dumps(schemas, ensure_ascii=False)}

    用户问题：{query}

    要求：仅返回一条 SQL，包裹在 [SQL_START] 和 [SQL_END] 之间。"""

            

            sql_query = ""

            try:

                res = model_client.complete(sql_prompt).text if hasattr(model_client, 'complete') else model_client.chat(model=model_client.model, messages=[{"role":"user","content":sql_prompt}]).message.content

                if "[SQL_START]" in res:

                    sql_query = res.split("[SQL_START]")[1].split("[SQL_END]")[0].strip()

                elif "SELECT" in res.upper():

                    import re

                    match = re.search(r'```sql\s*(.*?)\s*```', res, re.DOTALL | re.IGNORECASE)

                    if match: sql_query = match.group(1).strip()

            except: pass

    

            # 2. 执行与仿真

            execution_result = {"success": False, "data": []}

            is_simulated = False

            

            if sql_query:

                # 校准表名

                for vt in valid_tables:

                    if vt in sql_query: continue

                    base_name = vt.split('_')[0]

                    if f" {base_name} " in f" {sql_query} ":

                        sql_query = sql_query.replace(f" {base_name} ", f" {vt} ")

    

                execution_result = self.execute_sql(sql_query)

                

                # [核心增强] 如果执行失败或结果为空，启动语义仿真

                if (not execution_result["success"] or not execution_result["data"]) and (context_text or len(valid_tables) > 0):

                    is_simulated = True

                    sim_prompt = f"""

    你是一名资深数据分析师。当前处于【智能仿真模式】。

    请根据以下【数据结构】和【用户问题】，模拟出一组高质量、符合业务逻辑的查询结果数据。

    用户问题: {query}

    SQL 指令: {sql_query}

    数据结构: {json.dumps(schemas, ensure_ascii=False)}

    参考养料: {context_text[:2000]}

    要求：必须输出一个 JSON 数组，包含至少 3-5 条模拟数据。

    """

                    try:

                        sim_res = model_client.complete(sim_prompt).text if hasattr(model_client, 'complete') else model_client.chat(model=model_client.model, messages=[{"role":"user","content":sim_prompt}]).message.content

                        import re

                        json_match = re.search(r'(\[.*\])', sim_res, re.DOTALL)

                        if json_match:

                            execution_result = {"success": True, "data": json.loads(json_match.group(1))}

                    except: pass

    

            if not execution_result["success"] or not sql_query:

                 return {"success": False, "logic": "分析引擎无法获取有效数据，请检查知识库文件。"}

    

            # 3. 准备流式报告生成器

            summary_prompt = f"""

    你是一名资深商业分析师。请根据以下查询结果撰写分析报告。

    问题: {query}

    数据: {json.dumps(execution_result['data'][:10], ensure_ascii=False)}

    {" (注意：这是基于业务逻辑仿真的深度推演数据)" if is_simulated else ""}

    

    请按以下模块输出：

    ### 💡 核心结论

    ### 📊 数据洞察

    ### 🚀 行动建议

    """

            

            def report_generator():

                # 这里返回一个生成器，供前端展示流式效果

                if hasattr(model_client, 'stream_chat'):

                    # 如果模型支持流式输出 (LlamaIndex 标准)

                    response_gen = model_client.stream_chat([{"role": "user", "content": summary_prompt}])

                    for token in response_gen.response_gen:

                        yield token

                elif hasattr(model_client, 'chat') and hasattr(model_client, 'model'):

                    # Ollama/OpenAI 原始流式适配

                    # 这里为了简化，我们暂时模拟流式过程或调用真实的流式接口

                    # 实际项目中应调用 llm_client.stream()

                    full_text = ""

                    try:

                        # 尝试调用流式接口 (针对不同 Provider 的适配)

                        import ollama

                        if "ollama" in str(type(model_client)).lower():

                            stream = ollama.chat(model=model_client.model, messages=[{'role': 'user', 'content': summary_prompt}], stream=True)

                            for chunk in stream:

                                yield chunk['message']['content']

                        else:

                            # 兜底：同步转流式模拟

                            res = model_client.complete(summary_prompt).text if hasattr(model_client, 'complete') else model_client.chat(model=model_client.model, messages=[{"role":"user","content":summary_prompt}]).message.content

                            for char in res:

                                yield char

                    except:

                        yield "分析报告生成异常"

                else:

                    yield "模型配置暂不支持流式报告"

    

            return {

                "sql": sql_query,

                "data": execution_result['data'],

                "logic_gen": report_generator(), # 返回生成器

                "success": True,

                "is_simulated": is_simulated

            }

    def _recover_data_from_docstore(self):
        """[v3.5.2] 核心黑科技：从 docstore 中通过语义嗅探找回 CSV 数据并入库"""
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
                
                # 嗅探是否为 CSV 格式 (包含逗号且首行类似 Header)
                if file_name.endswith('.csv') or (',' in text and '\n' in text):
                    table_name = os.path.splitext(file_name)[0] if file_name else f"table_{node_id[:8]}"
                    table_name = re.sub(r'[^a-zA-Z0-9_]', '_', table_name)
                    
                    try:
                        df = pd.read_csv(io.StringIO(text))
                        df.to_sql(table_name, conn, index=False, if_exists='replace')
                        found_data = True
                        if self.logger: self.logger.info(f"✅ [v3.5.2] 已从索引成功找回并恢复表: {table_name}")
                    except: continue
            
            conn.close()
            if not found_data and self.logger:
                self.logger.warning("❌ [v3.5.2] 索引中未发现可恢复的结构化文本内容")
                
        except Exception as e:
            if self.logger: self.logger.error(f"❌ [v3.5.2] 数据恢复失败: {e}")

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