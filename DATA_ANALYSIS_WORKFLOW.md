# 数据分析：双核联动开发流程与架构设计规范 (Data Analysis Workflow)

**版本**: v8.3.3 (Flagship Dual-Core Edition)
**核心原则**: 语义底座 + 结构化增强 (Shadow Mapping)，物理必闭环。

---

## 一、 业务架构 (Business Architecture)

在 v8.3.3 架构下，数据分析能力已进化为 **“全源归一化 (Source-Agnostic)”** 的智能引擎。

### 1. 场景双核联动
- **语义层 (Base Layer)**: 100% 的材料经过 RAG 切片与向量化。
- **逻辑层 (Augmented Layer)**:
  - **物理底座**: SQLite 影子库。
  - **知识图谱**: 增强版 `business_schema.json`，支持外部 DB 镜像导入。

---

## 三、 开发与构建流程 (v8.3.3 全源版)

### 阶段 1：归一化摄入 (Normalized Ingestion)
1. **源头分流**:
    - **文件/文本/网页**: 物理归档至 `raw_sources/`。
    - **外部数据库**: 通过 `DBIngestor` 镜像表数据至本地 `.csv` 文件。
2. **底座先行**: 首先触发全量 RAG 构建流程。
3. **配置审计**: 系统自动记录 `[Build Config]`。

### 阶段 2：智能探测与分流 (Detection & Branching)
1. **意图检查**: 读取 `st.session_state.kb_enable_data_analysis` 或 **自动触发开关**。
2. **真数据判定**: 扫描 `raw_sources/`，计算数值密度。

### 阶段 3：结构化影子映射 (Shadow Solidification)
1. **建模固化**: `df.to_sql()` 生成物理影子表。
2. **Schema 深度增强 (Schema Enhancement)**:
   - **物理画像**: 识别 PK、Enums、空值率。
   - **血缘推演**: 自动构建 `join_graph` 关联网络。

### 阶段 4：双核协同响应 (Dual-Core Inference)
1. **路由判断**: 识别用户提问。**若开启数据分析开关，系统将优先进行逻辑推演。**
2. **逻辑推演**:
   - **查图谱**: 优先查阅 `join_graph`。
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