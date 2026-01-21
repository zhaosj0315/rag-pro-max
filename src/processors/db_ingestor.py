import os
import json
import pandas as pd
import sqlite3
from typing import List, Dict, Any
from sqlalchemy import create_engine, text
from src.auth.connection_manager import ConnectionManager

class DBIngestor:
    """
    [v8.3.0] 数据库摄入器
    负责将远程异构数据库的表结构和数据镜像到本地知识库的 SQLite 中，
    从而适配后续的 SchemaEnhancer 和 DataAnalystEngine。
    """
    
    def __init__(self, persist_dir: str, logger=None):
        self.persist_dir = persist_dir
        self.logger = logger
        self.local_db_path = os.path.join(persist_dir, "business_data.db")
        self.conn_manager = ConnectionManager()
        
        # 确保目录存在
        if not os.path.exists(persist_dir):
            os.makedirs(persist_dir)

    def ingest(self, connection_alias: str, db_name: str, table_names: List[str], sync_mode: str = "SAMPLE") -> bool:
        """
        执行摄入流程
        :param sync_mode: "SCHEMA_ONLY" (仅结构) | "SAMPLE" (结构+采样)
        """
        try:
            # 1. 获取连接配置
            conns = self.conn_manager.load_connections()
            if connection_alias not in conns:
                raise ValueError(f"连接别名不存在: {connection_alias}")
            
            config = conns[connection_alias]
            
            # 2. 建立远程连接
            url = self.conn_manager.get_connection_url(config, db_override=db_name)
            remote_engine = create_engine(url)
            
            # 3. 建立本地连接
            local_conn = sqlite3.connect(self.local_db_path)
            
            if self.logger:
                self.logger.info(f"🔌 [DB Ingest] 开始从 {connection_alias}.{db_name} 同步 {len(table_names)} 张表 (模式: {sync_mode})")
            
            success_count = 0
            # [v8.3.1] 准备基础 Schema 结构，供后续增强引擎使用
            base_schema = {
                "macro_context": f"从数据库 {connection_alias}.{db_name} 同步的数据资产",
                "tables": {}
            }
            
            for table in table_names:
                try:
                    # A. 读取结构与数据
                    # ... (省略中间查询逻辑)
                    limit_clause = "LIMIT 1000" if sync_mode == "SAMPLE" else "LIMIT 0"
                    if config['type'] == 'SQL Server': limit_clause = "TOP 1000 *" if sync_mode == "SAMPLE" else "TOP 0 *"
                    
                    query = f"SELECT * FROM {table} {limit_clause}"
                    df = pd.read_sql(query, remote_engine)
                    
                    # B. 写入本地 SQLite
                    df.to_sql(table, local_conn, index=False, if_exists='replace')
                    
                    # C. 提取基础元数据 (v8.3.1 类型对齐)
                    cols = []
                    for col in df.columns:
                        dtype = str(df[col].dtype)
                        sql_type = "TEXT"
                        if "int" in dtype: sql_type = "INTEGER"
                        elif "float" in dtype or "decimal" in dtype: sql_type = "REAL"
                        cols.append({"name": col, "type": sql_type, "comment": f"数据库字段: {col}"})

                    base_schema["tables"][table] = {
                        "table_name": table,
                        "desc": f"从数据库同步的业务表: {table}",
                        "cols": cols
                    }
                    
                    success_count += 1
                    if self.logger:
                        self.logger.info(f"   ✅ 同步表: {table} ({len(df)} rows)")
                        
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"   ⚠️ 同步表 {table} 失败: {e}")
            
            local_conn.close()
            
            # D. 固化基础 Schema 文件
            schema_path = os.path.join(self.persist_dir, "business_schema.json")
            with open(schema_path, 'w', encoding='utf-8') as f:
                json.dump(base_schema, f, indent=4, ensure_ascii=False)
            
            # 4. 生成元数据文件 (标记这是一个 DB 来源的 KB)
            meta = {
                "source_type": "database",
                "connection": connection_alias,
                "database": db_name,
                "tables": table_names,
                "sync_mode": sync_mode,
                "sync_time": str(pd.Timestamp.now())
            }
            with open(os.path.join(self.persist_dir, "db_sync_meta.json"), 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
                
            return success_count > 0
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ [DB Ingest Fatal] 摄入流程崩溃: {e}")
            return False
