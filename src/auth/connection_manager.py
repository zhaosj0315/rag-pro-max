import os
import json
import base64
from typing import Dict, List, Optional
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

    def save_connection(self, alias: str, db_type: str, host: str, port: int, 
                       user: str, password: str, db_name: str) -> bool:
        """保存或更新连接配置"""
        try:
            current = self.load_connections()
            current[alias] = {
                "type": db_type,
                "host": host,
                "port": port,
                "user": user,
                "password": self._encrypt(password), # 存储时加密
                "database": db_name,
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
        db_target = db_override if db_override else config['database']
        
        if t == 'mysql':
            return f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{db_target}"
        elif t == 'postgresql':
            return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{db_target}"
        # 可扩展其他类型
        return ""

    def test_connection(self, config: Dict) -> tuple[bool, str]:
        """测试连接连通性"""
        try:
            url = self.get_connection_url(config)
            if not url: return False, "不支持的数据库类型"
            
            engine = create_engine(url, connect_args={'connect_timeout': 5})
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
            
            # 连接到默认库或系统库以查询列表
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
            
            # 过滤系统库
            exclude = {'information_schema', 'mysql', 'performance_schema', 'sys', 'postgres'}
            return [d for d in dbs if d.lower() not in exclude]
        except Exception as e:
            print(f"List DB error: {e}")
            return [config['database']] # 降级：仅返回配置的默认库

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
        """获取指定表的字段结构"""
        try:
            conns = self.load_connections()
            if alias not in conns: return []
            
            url = self.get_connection_url(conns[alias], db_override)
            engine = create_engine(url)
            from sqlalchemy import inspect
            inspector = inspect(engine)
            cols = inspector.get_columns(table_name)
            
            # 格式化输出
            result = []
            for c in cols:
                result.append({
                    "name": c['name'],
                    "type": str(c['type']),
                    "nullable": c.get('nullable', True),
                    "default": str(c.get('default', ''))
                })
            return result
        except:
            return []
