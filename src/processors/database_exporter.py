import os
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from src.auth.connection_manager import ConnectionManager
import logging

class DatabaseExporter:
    """
    [v2.5.0] 数据库导出引擎
    负责将数据库查询结果物料化为物理文件 (CSV)，
    作为 "Everything is a Source File" 架构的数据库源适配器。
    """

    def __init__(self, output_dir: str):
        """
        初始化导出器
        :param output_dir: 输出目录 (通常是 task_staging_dir)
        """
        self.output_dir = output_dir
        self.conn_manager = ConnectionManager()
        self.logger = logging.getLogger(__name__)
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

    def export(self, connection_alias: str, db_name: str, 
               sql_query: str = None, table_name: str = None, 
               output_filename: str = None, chunk_size: int = 10000) -> str:
        """
        执行查询并导出为 CSV 文件
        
        :param connection_alias: 连接配置别名
        :param db_name: 目标数据库名
        :param sql_query: 自定义 SQL 查询 (优先级高于 table_name)
        :param table_name: 目标表名 (如果 sql_query 为空则全表导出)
        :param output_filename: 指定输出文件名 (可选)
        :param chunk_size: 分块读取大小 (防止 OOM)
        :return: 生成的 CSV 文件的绝对路径
        """
        try:
            # 1. 准备连接
            conns = self.conn_manager.load_connections()
            if connection_alias not in conns:
                raise ValueError(f"连接别名不存在: {connection_alias}")
            
            config = conns[connection_alias]
            url = self.conn_manager.get_connection_url(config, db_override=db_name)
            engine = create_engine(url)
            
            # 2. 准备 SQL
            if not sql_query and not table_name:
                raise ValueError("必须提供 sql_query 或 table_name")
            
            final_sql = sql_query
            source_tag = "custom_sql"
            if not final_sql:
                # 简单的全表查询
                # 注意: 简单拼装仅适用于可信环境，复杂场景应注意 SQL 注入 (虽这是内部工具)
                final_sql = f"SELECT * FROM {table_name}"
                source_tag = table_name

            # 3. 准备文件名
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                # 格式: [DB]Alias_DB_Source_Time.csv
                safe_alias = "".join([c if c.isalnum() else "_" for c in connection_alias])
                safe_source = "".join([c if c.isalnum() else "_" for c in source_tag])
                output_filename = f"[DB]{safe_alias}_{db_name}_{safe_source}_{timestamp}.csv"
            
            output_path = os.path.join(self.output_dir, output_filename)
            
            # 4. 执行流式导出
            self.logger.info(f"开始导出数据库快照: {connection_alias}.{db_name} -> {output_path}")
            
            # 使用 pandas chunked read
            # connection 对象在 chunk iterator 期间需要保持打开吗? 
            # pd.read_sql 当使用 chunksize 时返回 iterator
            
            row_count = 0
            # 必须用 connect() 上下文，否则某些 DB 可能连接泄漏
            with engine.connect() as conn:
                # 使用 stream results 防止大结果集爆内存 (SQLAlchemy execution_options)
                # 但 pandas read_sql 封装得比较深，我们直接用 chunksize
                for i, chunk in enumerate(pd.read_sql(text(final_sql), conn, chunksize=chunk_size)):
                    mode = 'w' if i == 0 else 'a'
                    header = (i == 0)
                    chunk.to_csv(output_path, mode=mode, header=header, index=False, encoding='utf-8-sig')
                    row_count += len(chunk)
                    
            self.logger.info(f"导出完成: {row_count} 行")
            
            # 5. 生成伴生元数据文件 (可选，方便溯源)
            meta_path = output_path + ".meta"
            with open(meta_path, "w", encoding="utf-8") as f:
                f.write(f"Source: Database\n")
                f.write(f"Connection: {connection_alias}\n")
                f.write(f"Database: {db_name}\n")
                f.write(f"Query: {final_sql}\n")
                f.write(f"ExportTime: {datetime.now().isoformat()}\n")
                f.write(f"Rows: {row_count}\n")

            return output_path

        except Exception as e:
            self.logger.error(f"数据库导出失败: {str(e)}")
            raise e
