import os
import json
import base64
from typing import Dict, List, Optional, Any
from sqlalchemy import create_engine, text

class ConnectionManager:
    """
    [v8.3.0] 数据库连接管理器
    负责管理多源异构数据库的连接配置，支持加密存储与连通性测试。
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_path = os.path.join(config_dir, "db_connections.json")
        self._ensure_config_file()

    def _ensure_config_file(self):
        if not os.path.exists(self.config_path):
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump({}, f)

    def _encrypt(self, text: str) -> str:
        """简单的Base64混淆 (生产环境建议使用 Fernet)"""
        return base64.b64encode(text.encode()).decode()

    def _decrypt(self, text: str) -> str:
        return base64.b64decode(text.encode()).decode()

    def load_connections(self) -> Dict[str, Dict]:
        """加载所有连接配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 解密密码
                for alias, conf in data.items():
                    if 'password' in conf:
                        conf['password'] = self._decrypt(conf['password'])
                return data
        except Exception as e:
            return {}

    def get_connections_for_user(self, username: str) -> Dict[str, Dict]:
        """获取特定用户的连接配置 (支持权限隔离)"""
        all_conns = self.load_connections()
        
        # 管理员可以看到所有连接
        # 注意: 这里假设调用方已确认用户角色，或者我们在内部再次检查角色
        # 为了安全起见，这里仅基于用户名过滤。如果用户名是 'admin'，返回所有。
        # 实际生产中应结合 Role 检查，但此处保持简单约定 'admin' 为超级用户。
        if username == 'admin':
            return all_conns
            
        # 普通用户只能看到自己的连接
        user_conns = {}
        for alias, conf in all_conns.items():
            owner = conf.get('owner')
            # 只有当 owner 明确等于当前用户时才显示
            # Legacy (owner=None) 视为 Admin 所有，普通用户不可见
            if owner == username:
                user_conns[alias] = conf
                
        return user_conns

    def save_connection(self, alias: str, db_type: str, host: str, port: int, 
                       user: str, password: str, db_name: str, owner: str = None) -> bool:
        """保存或更新连接配置 (支持所有者隔离)"""
        try:
            current = self.load_connections()
            current[alias] = {
                "type": db_type,
                "host": host,
                "port": port,
                "user": user,
                "password": self._encrypt(password), # 存储时加密
                "database": db_name,
                "owner": owner, # [v8.7.0] 新增所有者字段
                "updated_at": str(os.path.getmtime(self.config_path)) if os.path.exists(self.config_path) else ""
            }
            
            # 存盘时重新加密所有密码
            save_data = {}
            for k, v in current.items():
                item = v.copy()
                if k != alias: # 刚添加的已经是加密过的，旧的被解密了需要重加密
                    item['password'] = self._encrypt(v['password'])
                else:
                    item['password'] = v['password'] # 已经是加密的
                save_data[k] = item
                
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False

    def delete_connection(self, alias: str) -> bool:
        """删除连接"""
        try:
            # 直接读取原始文件以避免反复加解密带来的复杂性
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if alias in data:
                del data[alias]
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                return True
            return False
        except:
            return False

    def get_connection_url(self, config: Dict, db_override: str = None) -> str:
        """生成 SQLAlchemy 连接字符串"""
        t = config.get('type', 'mysql').lower()
        db_target = db_override if db_override else config.get('database', '')
        
        user = config.get('user', '')
        pw = config.get('password', '')
        host = config.get('host', 'localhost')
        port = config.get('port', '')

        if t == 'mysql':
            return f"mysql+pymysql://{user}:{pw}@{host}:{port}/{db_target}"
        elif t == 'postgresql':
            return f"postgresql://{user}:{pw}@{host}:{port}/{db_target}"
        elif t == 'mssql':
            return f"mssql+pyodbc://{user}:{pw}@{host}:{port}/{db_target}?driver=ODBC+Driver+17+for+SQL+Server"
        elif t == 'clickhouse':
            return f"clickhouse://{user}:{pw}@{host}:{port}/{db_target}"
        elif t == 'sqlite':
            # 对于 SQLite，host 字段存储的是本地路径
            return f"sqlite:///{host}"
        elif t == 'maxcompute':
            return f"odps://{user}:{pw}@{db_target}/?endpoint={host}"
        elif t == 'oracle':
            # 使用 oracledb 瘦模式，格式: oracle+oracledb://user:pass@host:port/?service_name=base
            return f"oracle+oracledb://{user}:{pw}@{host}:{port}/?service_name={db_target}"
        elif t == 'duckdb':
            # 与 SQLite 类似，host 存储路径
            return f"duckdb:///{host}"
        elif t == 'snowflake':
            # 格式: snowflake://<user_login_name>:<password>@<account_identifier>/<database_name>/<schema_name>?warehouse=<warehouse_name>&role=<role_name>
            return f"snowflake://{user}:{pw}@{host}/{db_target}"
        
        return ""

    def test_connection(self, config: Dict) -> tuple[bool, str]:
        """测试连接连通性"""
        try:
            url = self.get_connection_url(config)
            if not url: return False, "不支持的数据库类型"
            
            # 特殊处理 SQLite，确保路径存在
            if config.get('type') == 'SQLite':
                if not os.path.exists(config.get('host', '')):
                    return False, "SQLite 数据库文件不存在"

            engine = create_engine(url, connect_args={'connect_timeout': 5} if config.get('type') != 'SQLite' else {})
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, "连接成功"
        except Exception as e:
            return False, str(e)

    def get_database_list(self, alias: str) -> List[str]:
        """[v8.3.1] 获取实例下的所有数据库列表"""
        try:
            conns = self.load_connections()
            if alias not in conns: return []
            config = conns[alias]
            
            if config['type'] == 'SQLite': return ["main"]

            url = self.get_connection_url(config)
            engine = create_engine(url)
            
            dbs = []
            with engine.connect() as conn:
                if config['type'] == 'MySQL':
                    res = conn.execute(text("SHOW DATABASES"))
                    dbs = [row[0] for row in res]
                elif config['type'] == 'PostgreSQL':
                    res = conn.execute(text("SELECT datname FROM pg_database WHERE datistemplate = false"))
                    dbs = [row[0] for row in res]
                elif config['type'] == 'ClickHouse':
                    res = conn.execute(text("SHOW DATABASES"))
                    dbs = [row[0] for row in res]
                else:
                    dbs = [config.get('database', 'default')]
            
            # 过滤系统库
            exclude = {'information_schema', 'mysql', 'performance_schema', 'sys', 'postgres', 'system'}
            return [d for d in dbs if str(d).lower() not in exclude]
        except Exception as e:
            print(f"List DB error: {e}")
            return [conns[alias].get('database', 'main')]

    def get_table_list(self, alias: str, db_override: str = None) -> List[str]:
        """获取指定连接(及库)的所有表名"""
        try:
            conns = self.load_connections()
            if alias not in conns: return []
            
            url = self.get_connection_url(conns[alias], db_override)
            engine = create_engine(url)
            from sqlalchemy import inspect
            inspector = inspect(engine)
            return inspector.get_table_names()
        except:
            return []

    def get_table_schema(self, alias: str, table_name: str, db_override: str = None) -> List[Dict]:
        """[v8.6.0 增强] 获取详细字段结构（含主键识别）"""
        try:
            conns = self.load_connections()
            if alias not in conns: return []
            
            url = self.get_connection_url(conns[alias], db_override)
            engine = create_engine(url)
            from sqlalchemy import inspect
            inspector = inspect(engine)
            
            cols = inspector.get_columns(table_name)
            pk = inspector.get_pk_constraint(table_name).get('constrained_columns', [])
            
            result = []
            for c in cols:
                result.append({
                    "字段名": c['name'],
                    "类型": str(c['type']),
                    "主键": "🔑" if c['name'] in pk else "",
                    "允许为空": "YES" if c.get('nullable', True) else "NO",
                    "默认值": str(c.get('default', '')) if c.get('default') else "-"
                })
            return result
        except:
            return []

    def get_table_sample(self, alias: str, table_name: str, db_override: str = None, limit: int = 50) -> List[Dict]:
        """获取数据采样 (增加至 50 行)"""
        try:
            conns = self.load_connections()
            if alias not in conns: return []
            
            url = self.get_connection_url(conns[alias], db_override)
            engine = create_engine(url)
            
            with engine.connect() as conn:
                # 兼容不同数据库的采样语法
                if conns[alias]['type'] == 'SQL Server':
                    query = text(f"SELECT TOP {limit} * FROM {table_name}")
                else:
                    query = text(f'SELECT * FROM "{table_name}" LIMIT {limit}')
                
                try:
                    res = conn.execute(query)
                except:
                    res = conn.execute(text(f"SELECT * FROM {table_name} LIMIT {limit}"))
                
                rows = [dict(row._mapping) for row in res]
                return rows
        except:
            return []

    def get_table_insights(self, alias: str, table_name: str, db_override: str = None) -> Dict[str, Any]:
        """[v8.6.0] 获取深度业务洞察 (行数、外键、统计)"""
        try:
            conns = self.load_connections()
            if alias not in conns: return {}
            
            url = self.get_connection_url(conns[alias], db_override)
            engine = create_engine(url)
            from sqlalchemy import inspect
            inspector = inspect(engine)
            
            # 1. 基础统计
            row_count = 0
            with engine.connect() as conn:
                res = conn.execute(text(f"SELECT count(*) FROM {table_name}"))
                row_count = res.fetchone()[0]
            
            # 2. 关联血缘 (外键)
            fks = inspector.get_foreign_keys(table_name)
            fk_list = []
            for fk in fks:
                fk_list.append({
                    "本地字段": ",".join(fk['constrained_columns']),
                    "目标表": fk['referred_table'],
                    "目标字段": ",".join(fk['referred_columns'])
                })
                
            return {
                "row_count": row_count,
                "foreign_keys": fk_list,
                "engine": getattr(engine.dialect, 'name', 'unknown')
            }
        except:
            return {}
