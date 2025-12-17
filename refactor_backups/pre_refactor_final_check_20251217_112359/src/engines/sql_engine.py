"""
Text-to-SQL 引擎 - 最小实现
将Excel/CSV转换为SQLite，支持自然语言查询
"""
import sqlite3
import pandas as pd
import os
from typing import Dict, Any, List

class SQLEngine:
    def __init__(self, db_path: str = "temp_uploads/data.db"):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        return self.conn
        
    def import_excel_csv(self, file_path: str, table_name: str = None) -> str:
        """导入Excel/CSV到SQLite"""
        if not table_name:
            table_name = os.path.splitext(os.path.basename(file_path))[0]
            
        # 读取文件
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            df = pd.read_csv(file_path)
            
        # 导入数据库
        with self.connect() as conn:
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            
        return f"✅ 已导入 {len(df)} 行数据到表 '{table_name}'"
        
    def get_schema(self) -> Dict[str, List[str]]:
        """获取数据库结构"""
        schema = {}
        with self.connect() as conn:
            cursor = conn.cursor()
            # 获取所有表名
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                schema[table_name] = columns
                
        return schema
        
    def text_to_sql(self, question: str, llm_client) -> str:
        """自然语言转SQL"""
        schema = self.get_schema()
        
        # 构建Prompt
        schema_text = "\n".join([
            f"表 {table}: {', '.join(columns)}" 
            for table, columns in schema.items()
        ])
        
        prompt = f"""
根据以下数据库结构，将用户问题转换为SQL查询：

数据库结构：
{schema_text}

用户问题：{question}

请只返回SQL语句，不要其他解释：
"""
        
        # 调用LLM生成SQL
        response = llm_client.complete(prompt)
        sql = response.text.strip()
        
        # 简单清理
        if sql.startswith('```sql'):
            sql = sql.replace('```sql', '').replace('```', '').strip()
            
        return sql
        
    def execute_sql(self, sql: str) -> Dict[str, Any]:
        """执行SQL查询"""
        try:
            with self.connect() as conn:
                df = pd.read_sql_query(sql, conn)
                return {
                    "success": True,
                    "data": df.to_dict('records'),
                    "rows": len(df),
                    "columns": list(df.columns)
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql": sql
            }
