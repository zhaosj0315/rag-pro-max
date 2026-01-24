import sqlite3
import pandas as pd
import json
import os
from typing import Dict

class SchemaEnhancer:
    """
    [v8.2.0] Schema 增强引擎
    负责在构建阶段对物理表进行深度画像，提取血缘关系、主键约束和枚举值，
    将 business_schema.json 升级为具备业务导航能力的“实体关系图谱”。
    """
    
    def __init__(self, db_path: str, schema_path: str, logger=None):
        self.db_path = db_path
        self.schema_path = schema_path
        self.logger = logger

    def enhance(self, model_client=None):
        """执行全量增强流程"""
        if not os.path.exists(self.db_path) or not os.path.exists(self.schema_path):
            if self.logger: self.logger.warning("❌ [Schema Enhancer] DB或Schema文件缺失，跳过增强")
            return

        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            conn = sqlite3.connect(self.db_path)
            
            # 1. 物理画像增强 (Primary Keys & Enums)
            schema = self._profile_tables(conn, schema)
            
            # 2. 血缘关系推演 (Join Graph)
            schema = self._infer_join_graph(conn, schema, model_client)
            
            # 3. 固化增强后的 Schema
            with open(self.schema_path, 'w', encoding='utf-8') as f:
                json.dump(schema, f, indent=4, ensure_ascii=False)
                
            if self.logger: self.logger.success(f"🧠 [Schema Enhancer] 知识库图谱增强完成 (Joins: {len(schema.get('join_graph', []))}, Enums: {len(schema.get('enums_registry', {}))})")
            
            conn.close()
            
        except Exception as e:
            if self.logger: self.logger.error(f"⚠️ [Schema Enhancer] 增强过程异常: {e}")

    def _profile_tables(self, conn, schema: Dict) -> Dict:
        """维度一：物理特征画像 (兼容无数据场景)"""
        if 'enums_registry' not in schema: schema['enums_registry'] = {}
        
        tables = schema.get('tables', {})
        for t_name, t_info in tables.items():
            if t_info.get('is_virtual', False): 
                # 虚拟表直接走语义推测
                self._profile_tables_semantic(t_name, t_info, schema)
                continue
            
            try:
                # 检查表是否存在且有数据
                cursor = conn.cursor()
                try:
                    row_count = cursor.execute(f'SELECT count(*) FROM "{t_name}"').fetchone()[0]
                except:
                    row_count = 0
                
                if row_count == 0:
                    if self.logger: self.logger.info(f"   ℹ️ 表 '{t_name}' 无数据，切换至语义特征推测")
                    self._profile_tables_semantic(t_name, t_info, schema)
                    continue

                # 使用 Pandas 读取全量数据进行画像 (针对小规模数仓优化)
                df = pd.read_sql(f'SELECT * FROM "{t_name}" LIMIT 5000', conn)
                
                # A. 主键识别
                if row_count > 0:
                    pk_candidates = []
                    for col in df.columns:
                        if df[col].nunique() == row_count:
                            pk_candidates.append(col)
                    
                    if pk_candidates:
                        # 优先选择包含 id/code 的字段，或第一个字段
                        best_pk = next((c for c in pk_candidates if 'id' in c.lower() or 'code' in c.lower()), pk_candidates[0])
                        t_info['primary_key'] = best_pk
                        # 标记表角色：有主键通常是 Dim 或 Master 表，否则可能是 Fact
                        t_info['role'] = 'Dimension' if row_count < 1000 else 'Fact'
                
                # B. 枚举提取
                for col in df.columns:
                    # 仅针对文本类字段
                    if df[col].dtype == 'object':
                        distinct_vals = df[col].dropna().unique().tolist()
                        # 阈值：少于 30 个且少于行数的 20%
                        if 0 < len(distinct_vals) < 30 and len(distinct_vals) < row_count * 0.2:
                            # 存入全局注册表
                            registry_key = f"{t_name}.{col}"
                            schema['enums_registry'][registry_key] = [str(v) for v in distinct_vals]
                            # 在列定义中标记
                            for c_def in t_info.get('cols', []):
                                if c_def['name'] == col:
                                    c_def['has_enum'] = True
            except Exception as e:
                if self.logger: self.logger.warning(f"   ⚠️ 画像失败 {t_name}: {e}")
                
        return schema

    def _profile_tables_semantic(self, t_name: str, t_info: Dict, schema: Dict):
        """[Fallback] 语义特征推测：基于命名规则猜测主键和枚举"""
        cols = t_info.get('cols', [])
        
        # 1. 猜测主键
        # 规则：名字叫 id, code, pk，或者 {table_name}_id
        pk_candidates = [c['name'] for c in cols if c['name'].lower() in ['id', 'code', 'pk', 'uuid'] or c['name'].lower() == f"{t_name}_id".lower()]
        if pk_candidates:
            t_info['primary_key'] = pk_candidates[0]
            t_info['role'] = 'Dimension' # 只有定义的表通常被视为参考表
        
        # 2. 猜测枚举字段
        # 规则：名字包含 status, type, category, state, mode
        enum_keywords = ['status', 'type', 'category', 'state', 'mode', 'sex', 'gender', 'flag']
        for c in cols:
            c_name = c['name'].lower()
            if any(k in c_name for k in enum_keywords):
                c['has_enum'] = True
                # 尝试从注释中提取枚举值 (e.g. "状态 (1:新建, 2:完成)")
                comment = str(c.get('comment', ''))
                import re
                # 匹配 key:val 模式
                matches = re.findall(r'(\d+|[a-zA-Z]+)\s*[:=]\s*([^,;)]+)', comment)
                if matches:
                    registry_key = f"{t_name}.{c['name']}"
                    # 提取 value 部分作为枚举
                    extracted_enums = [m[1].strip() for m in matches]
                    if extracted_enums:
                        schema['enums_registry'][registry_key] = extracted_enums
                        if self.logger: self.logger.info(f"   🧠 [Semantic] 从注释提取枚举 {c['name']}: {extracted_enums}")

    def _infer_join_graph(self, conn, schema: Dict, model_client) -> Dict:
        """维度二：血缘关系推演 (物理+语义)"""
        join_graph = []
        tables = list(schema.get('tables', {}).keys())
        
        # 物理碰撞缓存
        col_values_cache = {} 
        
        # 1. 物理碰撞 (Physical Collision)
        # 遍历所有表对 (A, B)
        for i in range(len(tables)):
            for j in range(i + 1, len(tables)):
                t1, t2 = tables[i], tables[j]
                
                # 简单的同名/近名字段猜测
                cols1 = [c['name'] for c in schema['tables'][t1].get('cols', [])]
                cols2 = [c['name'] for c in schema['tables'][t2].get('cols', [])]
                
                potential_joins = []
                for c1 in cols1:
                    for c2 in cols2:
                        # 规则：名字相同，或者一个包含另一个 (e.g. user_id vs id)
                        is_same_name = c1.lower() == c2.lower()
                        is_fk_naming = (c1.lower() == f"{t2}_id".lower()) or (c2.lower() == f"{t1}_id".lower())
                        
                        if (is_same_name or is_fk_naming) and ('id' in c1.lower() or 'code' in c1.lower()):
                            potential_joins.append((c1, c2))
                
                # 验证潜在关联
                for c1, c2 in potential_joins:
                    # TODO: 这里可以加物理数据重合度校验 (set intersection)
                    # 暂时先用名称强规则作为 v1.0
                    join_graph.append({
                        "source": f"{t1}.{c1}",
                        "target": f"{t2}.{c2}",
                        "type": "Physical-Inferred",
                        "confidence": 0.8
                    })

        # 2. 语义补充 (LLM Semantic Inference)
        # 如果物理碰撞没找到关联，且有 LLM，尝试用 LLM 分析
        if not join_graph and model_client:
            prompt = f"""分析以下数据表及其字段，推断它们之间可能的关联键（Foreign Keys）。
            
            表结构:
            {json.dumps({t: schema['tables'][t] for t in tables}, ensure_ascii=False)}
            
            要求：
            1. 找出所有可能的 JOIN 关系
            2. 格式：TableA.ColumnX = TableB.ColumnY
            
            只返回 JSON 数组: [{{"source": "Table.Col", "target": "Table.Col"}}]"""
            
            try:
                res = model_client.complete(prompt).text
                # 简单的 JSON 提取逻辑
                import re
                match = re.search(r'(\[.*\])', res, re.DOTALL)
                if match:
                    llm_joins = json.loads(match.group(1))
                    for join in llm_joins:
                        join['type'] = "LLM-Inferred"
                        join['confidence'] = 0.6
                        join_graph.append(join)
            except: pass

        schema['join_graph'] = join_graph
        return schema
