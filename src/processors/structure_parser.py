import pandas as pd
import re
from typing import Dict, Any, List

class StructureParser:
    """结构解析器 - 专门识别和解析数据字典/定义文档"""

    def __init__(self):
        # 强信号关键词：出现在表头中
        self.schema_headers = {
            'field': ['字段名', '列名', 'field', 'column', 'col_name', 'column_name', '字段名称', '字段', '代码'],
            'type': ['类型', '数据类型', 'type', 'data_type', 'datatype', '字段类型'],
            'desc': ['描述', '说明', '含义', '注释', '备注', 'comment', 'description', 'desc', 'business_meaning', '中文名称', '字段中文']
        }
        
        # 弱信号关键词：出现在数据中
        self.type_values = ['int', 'integer', 'varchar', 'char', 'string', 'text', 'date', 'datetime', 'timestamp', 'float', 'double', 'decimal', 'boolean', 'bool', 'long']

    def is_data_dictionary(self, df: pd.DataFrame) -> bool:
        """
        判断一个 DataFrame 是否为数据字典
        判定逻辑：
        1. 表头包含特征词（如“字段名”、“类型”、“描述”）
        2. 数据行数较少（通常 < 500）
        3. 某一列的值高度疑似数据类型定义
        """
        if df.empty:
            return False
            
        # 1. 表头特征匹配
        headers = [str(c).lower().strip() for c in df.columns]
        matched_features = 0
        for key, keywords in self.schema_headers.items():
            if any(k in h for h in headers for k in keywords):
                matched_features += 1
        
        # 如果命中了2个以上特征（如同时有“字段”和“类型”），基本确认为字典
        if matched_features >= 2:
            return True

        # 2. 内容特征匹配 (辅助判断)
        # 检查是否有某一列，其内容大部分是数据类型关键词
        for col in df.columns:
            # 抽样前20行非空值
            sample_values = df[col].dropna().astype(str).str.lower().str.strip().tolist()[:20]
            if not sample_values: continue
            
            matches = sum(1 for v in sample_values if any(tk == v or tk in v for tk in self.type_values))
            if len(sample_values) > 0 and matches / len(sample_values) >= 0.6:
                # 高度疑似类型列
                if matched_features >= 1: # 只要有一个表头特征匹配，加上内容特征，也认为是字典
                    return True
        
        return False

    def parse(self, df: pd.DataFrame, file_name: str) -> Dict[str, Any]:
        """
        解析数据字典，提取表结构定义
        返回格式:
        {
            "tables": {
                "table_name": {
                    "desc": "表描述",
                    "cols": [{"name": "id", "type": "int", "comment": "主键"}],
                    "is_virtual": True
                }
            }
        }
        """
        headers = [str(c).lower().strip() for c in df.columns]
        
        # 1. 映射关键列
        col_map = {}
        for key, keywords in self.schema_headers.items():
            for i, h in enumerate(headers):
                if any(k in h for k in keywords):
                    col_map[key] = df.columns[i]
                    break
        
        # 必须找到“字段名”列，否则无法解析
        if 'field' not in col_map:
            # 尝试盲猜第一列
            col_map['field'] = df.columns[0]
        
        # 2. 提取结构
        cols = []
        for _, row in df.iterrows():
            name = str(row[col_map['field']]).strip()
            if not name or name.lower() == 'nan': continue
            
            # 清洗字段名 (只保留字母数字下划线)
            clean_name = re.sub(r'[^a-zA-Z0-9_]', '', name)
            if not clean_name: clean_name = name # 如果清洗后为空，保留原名
            
            dtype = str(row[col_map['type']]).strip() if 'type' in col_map else 'TEXT'
            comment = str(row[col_map['desc']]).strip() if 'desc' in col_map else ''
            
            cols.append({
                "name": clean_name,
                "type": dtype,
                "comment": comment
            })
            
        if not cols:
            return {}

        # 3. 推断表名 (从文件名或表内容)
        # 简单的做法：直接用文件名作为表名
        table_name = re.sub(r'[^a-zA-Z0-9_]', '_', os.path.splitext(file_name)[0]).lower()
        if table_name.startswith('dict_') or table_name.startswith('schema_'):
            table_name = table_name.replace('dict_', '').replace('schema_', '')
            
        return {
            "tables": {
                table_name: {
                    "desc": f"从字典文件解析: {file_name}",
                    "cols": cols,
                    "is_virtual": True,
                    "source_file": file_name
                }
            }
        }
import os
