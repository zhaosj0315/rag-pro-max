# RAG Pro Max 核心功能实现详述 (Core Feature Implementation)

**版本**: v8.9.0 (Flagship Unified Edition)
**状态**: 关键性资产 (永久保存)
**描述**: 本文档记录了 v8.9「精准抓取」逻辑及 v8.8「极简归一化」架构的底层实现逻辑、协同算法及物理闭环规范。

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

---

## 🕷️ 4. 精准层级爬取逻辑 (Level-0 Exponential Crawl)
v8.9.0 重新定义了递归爬取的层级语义，以解决深度扩散时的配额分配问题。

### 算法演进 (Algorithm Evolution)
1. **Level 0 (Seed Isolation)**: 种子 URL 被隔离处理。它不计入 Level 1 的 $n$ 个名额，仅作为初始 HTML 获取源。
2. **Exponential Distribution**: 采用 $n^{depth}$ 的配额分配。
   - **Level 1**: 从种子页提取出的链接中抓取前 $n$ 个。
   - **Level 2**: 从 Level 1 页面中进一步提取链接，抓取前 $n^2$ 个。
3. **Cross-Engine Consistency**: 同步 (`WebCrawler`)、异步 (`AsyncWebCrawler`)、并发 (`ConcurrentCrawler`) 三大引擎底层共享此递归逻辑，确保在不同性能模式下产出一致的文档集合。
- **Scope Guard**: 自动根据种子 URL 的域名及路径深度（如阿里云帮助文档的 `/help/zh/`）设定作用域锁，防止爬虫逃逸至无关域名。

---

## 📦 5. 全能并集摄入逻辑 (Omni-Ingestion Pipeline)
v9.0.0 引入了基于物理暂存区的“并集”收集算法，替代了原本基于优先级的互斥逻辑。

### 设计实现 (Design Details)
1.  **Staging Lifecycle**: 在新建知识库会话启动时，系统通过 `uuid` 生成唯一的 `task_staging_dir` 物理路径。
2.  **Staging Sync (`sync_to_staging`)**:
    *   **文件上传**: 捕获 `st.file_uploader` 状态，实时将缓存文件写入暂存区。
    *   **目录同步**: 调用 `os.walk` 递归扫描本地目录，将符合规则的文件物理拷贝至暂存区。
    *   **文本粘贴**: 将粘贴内容持久化为 `manual_pasted_{timestamp}.txt`。
3.  **Atomic Anchoring**: 在执行 `IndexBuilder.build()` 之前，强制将 `uploaded_path` 指向暂存区，实现多源到单源的平滑转换。
4.  **Self-Healing**: 自动检查暂存区的物理存在性，并在页面热重载时实现静默重建。
