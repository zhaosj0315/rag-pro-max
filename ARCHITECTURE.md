# RAG Pro Max v5.6.8 企业级系统架构文档

**版本**: v5.6.8 (Production Stability Edition)  
**更新日期**: 2026-01-13  
**核心特性**: URL 现场恢复、路径深度自愈 (Self-healing)、高保真文档爬取、666 权限日志引擎

---

## 🏗️ 核心架构演进 (v5.6.x)

### 1. 状态管理层 (State Management - Persistent Memory)
- **URL Parameter Sync**: 将活跃的 `kb_id` 和 `sess_id` 实时同步至浏览器地址栏。应用启动时优先通过 URL 恢复现场，实现“刷新即秒回”。
- **Memory-Priority Titles**: 引入内存补偿机制，侧边栏标题在对话生成瞬间即可反映内容变化，不再依赖异步落盘延迟。

### 2. 系统韧性层 (Resilience Layer - Self-healing)
- **Path Self-healing Engine**: 针对 UI 脱敏后的短名，实现了模糊前缀匹配算法。系统能自动识别 `admin_` 等前缀并修正物理挂载路径，解决“docstore.json 丢失”问题。
- **Auto-Permission Hardening**: 日志引擎内置 `chmod 666` 逻辑，确保不同所有权进程（Root/Standard）产生的日志能被所有标准用户读取显示。

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

