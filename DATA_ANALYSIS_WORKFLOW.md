# 数据分析模式：开发流程与架构设计规范 (Data Analysis Workflow)

**版本**: v1.0.0
**核心原则**: 构建即就绪，物理必闭环。

---

## 一、 业务架构 (Business Architecture)

数据分析模式的设计目标是为用户提供一个“从模糊需求到物理底座，再到结构化洞察”的完整链路。

### 1. 场景双轨制
- **场景 A：数据驱动 (Data-Driven)**
  - 输入：CSV, XLSX, SQL 导出文件。
  - 核心：提取真实物理结构，直接固化。
- **场景 B：需求驱动 (Requirement-Driven)**
  - 输入：业务 PRD, 指引手册, 纯文本需求。
  - 核心：通过 LLM 推演逻辑模型 (Logical Model) -> 映射为物理模型 (Physical Model) -> 仿真数据填充。

---

## 二、 基础架构设计 (Infrastructure Design)

### 1. 物理存储层 (Storage)
- **数据库**: SQLite (轻量级、无盘化/本地文件、事务支持)。
- **文件路径**: `vector_db_storage/{KB_NAME}/business_data.db`。
- **Schema 存储**: `vector_db_storage/{KB_NAME}/business_schema.json`。

### 2. 仿真引擎 (Simulation Engine)
- **逻辑**: 基于提取的 `is_virtual` 字段。
- **注入策略**: 针对日期、数值、分类字段，AI 生成符合业务逻辑分布的样本（如销售额在 100-10000 之间，日期在最近一年内）。

---

## 三、 开发与构建流程 (Development Workflow)

### 阶段 1：扫描与识别 (Scan & Identify)
1. **分类**: 区分“结构化数据文件”与“半结构化/非结构化文档”。
2. **初步清理**: 归一化表名（去除非法字符），转换编码。

### 阶段 2：建模与固化 (Modeling & Solidification)
1. **有数固化**: `df.to_sql()`。
2. **逻辑提取**: 对文档进行递归摘要，提取 `TABLE` 定义、`COLUMN` 定义及业务释义。
3. **合并蓝图**: 将物理表与逻辑表合并为一份 `unified_schema`。

### 阶段 3：底座自愈与仿真 (Self-Healing & Simulation)
1. **环境自检**: `_ensure_sandbox_ready()`。
2. **造数闭环**: 如果表为空或仅有逻辑定义，立刻启动 `_populate_mock_data()`。
3. **就绪声明**: 打印 `✨ [Success] 数据分析物理底座构建完成`。

### 阶段 4：对话与推演 (Query & Inference)
1. **SQL 分步生成**: 拆解多级分析任务。
2. **动态执行**: 捕获 `sqlite3` 报错，利用 AI 自动修正 SQL。
3. **可视化适配**: 采样 Top 5 数据并格式化为图表前端可读的 JSON 结构。

---

## 四、 运维与演进规范

1. **不可删除性**: `business_data.db` 与 `business_schema.json` 是知识库的核心资产，非重建请求不可删除。
2. **版本一致性**: 每次通过 `apppro.py` 构建完成后，必须更新 `version.json` 中的构建指纹。

---

## 📑 开发者 Checkbox
- [ ] 构建完成后，`business_data.db` 文件是否存在？
- [ ] `business_schema.json` 是否包含业务背景描述？
- [ ] 针对虚拟表，生成的模拟数据是否满足统计学分布？
- [ ] 历史对话是否能完整重绘 SQL 可视化看板？
