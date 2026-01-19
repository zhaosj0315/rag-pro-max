# RAG Pro Max 核心功能实现详述 (Core Feature Implementation)

**版本**: v6.9.5 (Flagship Purified Edition)
**状态**: 关键性资产 (永久保存)
**描述**: 本文档记录了系统七大核心功能的底层实现逻辑、业务架构及技术细节。

---

## 1. 📂 文件上传 (File Upload)
实现“构建即就绪”的高性能 RAG 索引管线。

- **扫描与预处理**：递归扫描上传目录，利用文件哈希（SHA-256）建立增量更新机制，避免重复处理。
- **并发解析 (Parallel Processing)**：
  - **CPU 密集型 (PDF/Docx)**：使用 `ProcessPoolExecutor` 多进程加速文本提取。
  - **I/O 密集型 (API 调用)**：使用线程池处理 OCR 或元数据注入。
- **嵌入与入库**：基于 `LlamaIndex` 框架，直接通过 `load_embedding_model` 调用核心 Service，构建 `VectorStoreIndex`。
- **元数据绑定**：在构建时自动注入 `file_path`, `creation_date` 等元数据，支持后续的精准溯源。

## 2. 📝 粘贴文本 (Paste Text)
... (此处逻辑未变) ...

## 3. 🔗 网址抓取 (Web Crawl)
饱和式、防封控的内容抓取引擎。

- **饱和式抓取管线**：采用基于 Full URL Scope 的队列逻辑。
- **物理化对齐**：抓取后的 Markdown 文件名直接映射 URL 路径，并自动设置 macOS `com.apple.metadata:kMDItemWhereFroms` 扩展属性。

## 4. 🔍 智能搜索 (Keyword Search)
... (此处逻辑未变) ...

## 5. 📊 数据分析 (Data Analysis) - Strategic Workshop 3.0
... (此处逻辑未变) ...

## 🛡️ 6. 旗舰治理中心 (Flagship Governance)
物理生命周期与个体安全策略的深度融合系统。

- **个体安全调节舱 (Individual Cabin)**：
  - **单兵策略**：支持三级 TTL 判定逻辑，允许为特定用户设置专属会话有效期。
  - **定点熔断**：通过 `revoke_user_sessions` 接口实现“手术刀式”的即时通信断开。
- **全合规扫描引擎**：
  - **自动化诊断**：秒级探测索引损坏、容量超限（>500MB）及长期闲置（>30天）资产。
- **时序风险画像**：基于行为加权评分（Critical=50, Warning=10, Info=1）生成 24 小时风险脉搏。

## 🧼 7. 架构净化与逻辑唯一化 (Architecture Purification)
系统的稳定性保障基石。

- **扁平化心脏**：废弃 `MainController` 类架构，回归 `apppro.py` 扁平化流式架构，减少 15% 的模块加载开销。
- **逻辑唯一性**：物理清除 25+ 冗余模块，确保全系统业务逻辑只有一条物理路径，彻底根除版本误用与 `ModuleNotFoundError`。
- **高性能日志**：全面转向 `LogManager` 异步日志体系，废弃旧版 `logger.py` 包装器。

---

## 📑 管理规范
- **修改限制**：本文档属于核心业务逻辑定义，任何对底层实现的修改必须同步更新本文档。
- **永久保存**：禁止在清理脚本中包含此文档。
