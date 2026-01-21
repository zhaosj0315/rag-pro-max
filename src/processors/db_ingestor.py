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
        [v8.3.2 重构] 数据库镜像模式
        将远程表镜像为本地 CSV 文件，从而 100% 复用后续的“文件构建”逻辑。
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
            
            if self.logger:
                self.logger.info(f"🔌 [DB Ingest] 镜像下载模式启动: {connection_alias}.{db_name} (Tables: {len(table_names)})")
            
            success_count = 0
            
            for table in table_names:
                try:
                    # A. 拉取数据 (采样或全量结构)
                    limit_clause = "LIMIT 1000" if sync_mode == "SAMPLE" else "LIMIT 0"
                    query = f"SELECT * FROM {table} {limit_clause}"
                    
                    df = pd.read_sql(query, remote_engine)
                    
                    # B. 落地为 CSV 材料 (归一化入口)
                    # 我们将表存为 csv，存放在 persist_dir 下
                    csv_path = os.path.join(self.persist_dir, f"{table}.csv")
                    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                    
                    success_count += 1
                    if self.logger:
                        self.logger.info(f"   📥 已导出镜像文件: {table}.csv ({len(df)} rows)")
                        
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"   ⚠️ 镜像导出 {table} 失败: {e}")
            
            # 💡 这里不再生成 business_data.db 或 business_schema.json
            # 后续调用标准构建流程时，系统会识别这些 CSV 并自动完成所有高级工作
            
            return success_count > 0
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ [DB Ingest Fatal] 镜像准备失败: {e}")
            return False
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
