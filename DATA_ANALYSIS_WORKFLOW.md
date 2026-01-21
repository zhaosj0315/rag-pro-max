# 数据分析：双核联动开发流程与架构设计规范 (Data Analysis Workflow)

**版本**: v8.2.0 (Flagship Dual-Core Edition)
**核心原则**: 语义底座 + 结构化增强 (Shadow Mapping)，物理必闭环。

---

## 一、 业务架构 (Business Architecture)

在 v8.2.0 架构下，数据分析能力已进化为 **“图谱驱动 (Graph-Driven)”** 的智能引擎。

### 1. 场景双核联动
- **语义层 (Base Layer)**: 100% 的材料经过 RAG 切片与向量化。
- **逻辑层 (Augmented Layer)**:
  - **物理底座**: SQLite 影子库。
  - **知识图谱**: 增强版 `business_schema.json`，包含主键、枚举与血缘拓扑。

---

## 二、 基础架构设计 (Infrastructure Design)

### 1. 物理存储层 (Storage)
- **数据库**: SQLite。
- **图谱元数据**: `vector_db_storage/{KB_NAME}/business_schema.json` (v8.2.0 Enhanced)。

---

## 三、 开发与构建流程 (v8.2.0 图谱版)

### 阶段 1：归一化摄入 (Normalized Ingestion)
1. **统一路径**: 无论是爬虫还是上传，文件统一归档至 `raw_sources/`。
2. **底座先行**: 首先触发全量 RAG 构建流程。
3. **配置审计**: 系统自动记录 `[Build Config]`。

### 阶段 2：智能探测与分流 (Detection & Branching)
1. **意图检查**: 读取 `st.session_state.kb_enable_data_analysis`。
2. **真数据判定**: 扫描 `raw_sources/`，计算数值密度。

### 阶段 3：结构化影子映射 (Shadow Solidification)
1. **建模固化**: `df.to_sql()` 生成物理影子表。
2. **Schema 深度增强 (Schema Enhancement)**:
   - **物理画像**: 识别 PK、Enums、空值率。
   - **血缘推演**: 自动构建 `join_graph` 关联网络。
   - **语义兜底**: 若无数据，基于字段命名规则推测业务逻辑。

### 阶段 4：双核协同响应 (Dual-Core Inference)
1. **路由判断**: 识别用户提问是定性（RAG）还是定量（SQL）。
2. **逻辑推演**:
   - **查图谱**: Planner 优先查阅 `join_graph` 规划路径。
   - **原子拆解**: Filter -> Join -> Aggregation。
   - **质量诊断**: 零值自愈 + 幻觉排查。

---

## 四、 运维与演进规范

1. **资源治理**: **旗舰治理中心** 必须同时巡检 `.db` 数据库与向量索引的健康度。
2. **不可删除性**: `business_data.db` 是实现“数文对照”的核心底座，禁止单独删除。

---

## 📑 开发者 Checkbox
- [ ] RAG 索引构建是否成功？
- [ ] 勾选高级选项后，`business_data.db` 是否在 KB 目录下生成？
- [ ] SQL 生成是否包含业务语义注释（来自 RAG 提取）？
- [ ] 旗舰治理中心是否能正确识别该“双核”库的容量状态？