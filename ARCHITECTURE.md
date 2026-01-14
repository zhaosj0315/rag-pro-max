# RAG Pro Max v6.2.2 企业级系统架构文档

**版本**: v6.2.2 (Mirroring & Global Insights Edition)  
**更新日期**: 2026-01-14  
**核心特性**: 全维度对话镜像、中英双语业务发现、Retina 级图表导出、多模式严格隔离

---

## 🏗️ 核心架构演进 (v6.2.x)

### 1. 资产导出镜像层 (Mirroring & Export Pipeline)
- **Multi-Perspective Export**: 实现了同步绘图管线。在导出阶段，系统会针对每个 `stage` 重新调用绘图引擎，产出 AI、Bar、Line 三种视角的 PNG 和 HTML。
- **Markdown Lineage Reconstruction**: 消息转换为 MD 时，通过上下文感知的映射算法，将内存中的统计信息、引用源以及物理图片路径重新编排，实现离线镜像级体验。

### 2. 可视化呈现层 (Smart Visualization Engine)
- **Bilingual Insight Engine**: 在建议生成阶段引入 `CN/EN` 双语提示词约束，并采用双层 UI 渲染技术（Bold Head + Italic Caption）。
- **Dynamic Tab Router**: 采用多态路由机制，支持 6 种以上可视化组件的动态挂载与参数双向绑定。

### 3. 数据持久化层 (Storage Sovereignty Hardening)
- **Isolation Protection**: RAG 索引构建器（NEW 模式）现在仅对 `.json` 文件执行精准清理，不再调用 `shutil.rmtree`，确保 `raw_sources/` 和 `business_data.db` 的物理共存。
- **Mode Isolation**: 实现了“显式触发”逻辑，强制切断非分析模式下的 DB 建模链路。

---

## 🧩 核心流程演进 (v5.6.8)

### 1. 对话现场恢复流程 (Persistent Memory)
```
页面刷新 / 重新登录
    ↓
获取 URL 参数 (kb_id, sess_id)
    ↓
路径自愈引擎 (寻找带前缀的物理路径)
    ↓
加载历史 JSON 记录 (HistoryManager)
    ↓
内存补偿渲染 (同步侧边栏标题)
    ↓
挂载知识库向量索引 (RAG Ready)
```

### 2. 高保真爬取流程 (Advanced Crawl)
```
输入 URL 
    ↓
路径前缀锁定 (锁定 Scope 防止扩散)
    ↓
html2text 引擎 + body_width=0
    ↓
URL 路径映射文件名 (结构化展示)
    ↓
自动化元数据打标 (Mac xattr 来源追踪)
```

