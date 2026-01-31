# 数据分析：双核联动开发流程与架构设计规范 (Data Analysis Workflow)

**版本**: v9.8.0 (DA-ECP V4.5 Edition)
**核心原则**: 构建即理解 (Construction as Understanding) + 动静分离 (JIT Generation)。

---

## 一、 业务架构 (Business Architecture)

在 v9.8.0 架构下，数据分析能力升级为 **DA-ECP V4.5 (Data Analysis Enhanced Construction Protocol)**，实现了从“被动解析”到“主动建模”的认知跃迁。

### 1. 场景双核联动
- **语义层 (Base Layer)**: 100% 的材料经过 RAG 切片与向量化。
- **逻辑层 (Cognitive Layer)**:
  - **物理底座**: SQLite 影子库 (支持 Solid/Virtual 混合态)。
  - **知识图谱**: 增强版 `business_schema.json`，包含微观画像 (Stats/Enums) 与血缘关系。

---

## 三、 开发与构建流程 (DA-ECP V4.5 标准)

### 1. 全源嗅探与仲裁 (Sniffing & Arbitration)
构建开始时，`DataAnalystEngine` 对每个文件进行特征嗅探：
- **Solid Table (实体数据)**: 判定为真实业务记录 (CSV/Excel)。
- **Virtual Table (虚拟定义的)**: 判定为数据字典或 Schema 定义文档。
- **Terminal Feedback**: 终端通过图标 `📦` (Solid) 和 `📐` (Virtual) 实时反馈仲裁结果。

### 2. 双轨并行处理 (Dual-Track Processing)
- **Track A: 全息搬运 (Micro-Profiling)**
    - 针对 **Solid Tables**。
    - **动作**: 入库的同时，计算字段级特征（空值率、Min/Max/Avg、枚举值分布）。
    - **产出**: 包含丰富统计元数据的物理表定义。
- **Track B: 建筑师模式 (Structure Parsing)**
    - 针对 **Virtual Tables**。
    - **动作**: 调用 `StructureParser` 提取表名、字段名、类型及注释。
    - **产出**: 仅在 SQLite 中创建空表结构 (Schema Only)，绝不生成模拟数据。

### 3. 语义建模与固化 (Semantic Modeling & Solidification)
- **血缘推演**: LLM 基于提取的画像，推演表与表之间的 Join 关系。
- **蓝图固化**: 将所有实体定义、统计特征及关联关系写入 `business_schema.json`。
- **动静分离**: 构建结束时，`business_data.db` 仅包含必要的实体数据和空的虚拟表结构。

### 4. 问答时：JIT 动态造数 (Just-In-Time Generation)
当用户提问触发分析意图时：
1. **完整性检查**: 系统检查涉及的表是否为空 (Virtual Table)。
2. **按需造数**: 若为空，则基于 Schema 定义和用户问题上下文，现场生成 30 条高相关性的模拟数据。
3. **实证分析**: 执行 SQL 查询，验证逻辑并返回结果。

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
