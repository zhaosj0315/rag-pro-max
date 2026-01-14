# RAG Pro Max v5.9.4 企业级系统架构文档

**版本**: v5.9.4 (Advanced Visualization Edition)  
**更新日期**: 2026-01-14  
**核心特性**: 智能可视化画板、SQL 真数采样、多存储引擎共存隔离

---

## 🏗️ 核心架构演进 (v5.9.x)

### 1. 可视化呈现层 (Smart Visualization Engine)
- **AI Recommendation Layer**: 引入绘图专家代理，根据 SQL 执行结果的语义特征自动推荐 `plotly.express` 渲染方案。
- **Dynamic Tab Router**: 采用多态路由机制，支持 6 种以上可视化组件的动态挂载与参数双向绑定。

### 2. 数据持久化层 (Storage Sovereignty Hardening)
- **Isolation Protection**: RAG 索引构建器（NEW 模式）现在仅对 `.json` 文件执行精准清理，不再调用 `shutil.rmtree`，确保 `raw_sources/` 和 `business_data.db` 的物理共存。
- **Build Sequence Reordering**: 实现了“先建目录、后存数据”的流水线，彻底解决存储竞争导致的资产丢失。

### 3. AI 策略层 (AI Strategy & Sampling)
- **Real-Data Injection**: 在 Prompt 组装阶段增加“采样垫片”，自动提取物理表前 2 行数据注入 LLM 上下文，确保生成 SQL 的 100% 语境兼容。

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

