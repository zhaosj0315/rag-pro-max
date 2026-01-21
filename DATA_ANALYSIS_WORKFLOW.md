# 数据分析：双核联动开发流程与架构设计规范 (Data Analysis Workflow)

**版本**: v8.1.3 (Flagship Dual-Core Edition)
**核心原则**: 语义底座 + 结构化增强 (Shadow Mapping)，物理必闭环。

---

## 一、 业务架构 (Business Architecture)

在 v8.1.1 架构下，数据分析能力已完全**内化**为知识库的一项基础属性。

### 1. 场景双核联动
- **语义层 (Base Layer)**: 100% 的材料经过 RAG 切片与向量化。
- **逻辑层 (Augmented Layer)**: 仅当用户在构建时勾选 **「💎 智能数据分析」** 时生成。

---

## 二、 基础架构设计 (Infrastructure Design)

### 1. 物理存储层 (Storage)
- **数据库**: SQLite。
- **文件路径**: `vector_db_storage/{KB_NAME}/business_data.db`。
- **协同存储**: 与 `index_store.json` (RAG索引) 同级并存。

---

## 三、 开发与构建流程 (v8.1.3 审计版)

### 阶段 1：归一化摄入 (Normalized Ingestion)
1. **统一路径**: 无论是爬虫还是上传，文件统一归档至 `raw_sources/`。
2. **底座先行**: 首先触发全量 RAG 构建流程。
3. **配置审计**: 系统自动记录 `[Build Config]`，锁定本次构建是否开启了数据分析。

### 阶段 2：智能探测与分流 (Detection & Branching)
1. **意图检查**: 读取 `st.session_state.kb_enable_data_analysis` 标志位（来自高级选项）。
2. **真数据判定 (Validator)**: 扫描 `raw_sources/`，计算数值密度。
3. **分流**: 
   - 勾选且为真数据 ➡ 进入「结构化建模」。
   - 未勾选或低分表格 ➡ 仅保留语义索引。

### 阶段 3：结构化影子映射 (Shadow Solidification)
1. **建模固化**: `df.to_sql()` 生成物理影子表。
2. **自愈仿真**: 针对只有逻辑定义（需求文档）的表，启动 AI 仿真注入。
3. **过程双写**: 所有 Schema 提取日志同步写入 `.jsonl` 文件。

### 阶段 4：双核协同响应 (Dual-Core Inference)
1. **路由判断**: 识别用户提问是定性（RAG）还是定量（SQL）。
2. **逻辑推演 (v8.1.2)**:
   - **原子拆解**: Planner 强制执行 Filter -> Join -> Aggregation 路径。
   - **精准选表**: 应用 Fact-First 策略消除字段歧义。
   - **质量诊断**: 若 SQL 结果为空，自动触发 JOIN Key 幻觉排查。
3. **数文对照**: 
   - 输出 SQL 计算结论。
   - 输出 RAG 文本证据（支持跳转至原文对应页码）。

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