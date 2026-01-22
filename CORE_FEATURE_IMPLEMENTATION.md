# RAG Pro Max 核心功能实现详述 (Core Feature Implementation)

**版本**: v8.8.0 (Flagship Unified Edition)
**状态**: 关键性资产 (永久保存)
**描述**: 本文档记录了 v8.8「极简归一化」架构的底层实现逻辑、协同算法及物理闭环规范。

---

## 🧬 1. 双核组装逻辑 (Dual-Core Assembly)
系统将 RAG (语义核) 与 SQL (逻辑核) 从平行的孤岛状态提升为层级化的协同状态。

### 核心处理算法 (Pipeline Workflow)
1. **标准化摄入**: 通过 `src/processors/upload_handler.py` 收集全源文件。
2. **底座构建 (Must-pass)**: 
   - 调用 `IndexBuilder.build()` 执行 RAG 管线。
   - 所有文件（含表格）被向量化并存入 `index_store.json`。
3. **意图审查 (Audit)**:
   - 检查 `enable_data_analysis` 标志位。
4. **增强映射 (Augmented Path)**:
   - 若标志位为真，调用 `DataAnalystEngine.process_files()`。
   - 对 `raw_sources/` 目录执行物理扫描与真数据验证。
   - 生成 `business_data.db` 物理库。

---

## 📂 2. 归一化摄入管线 (Normalized Ingestion)
三大全能入口（文件、互联网、数据库）最终导向同一个物理出口：

- **Markdown 脱水**: 所有非结构化源统一转化为 `.md` 格式。
- **物理化对齐**: 必须先执行 `shutil.copy2` 到 `raw_sources/` 进行归档，随后才触发 SQL 引擎。
- **元数据同步**: RAG 的摘要信息与 SQL 的 Schema 定义共享同一个 `manifest.json` 元数据声明。

---

## 🧼 3. 架构鲁棒性与净化 (Robustness)
- **逻辑单点**: 删除了所有残留的“模式选择”旧逻辑，确立了以 `process_knowledge_base_logic` 为核心的唯一编排器。
- **物理闭环**: 同一个知识库 ID 文件夹内的双向引用通过物理文件 ID (`doc_id` <-> `row_id`) 实现初步关联。
