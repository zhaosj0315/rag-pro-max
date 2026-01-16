# RAG Pro Max v6.6.5 企业级系统架构文档

**版本**: v6.6.5 (Repair & Enhancement Edition)  
**更新日期**: 2026-01-16  
**核心特性**: 饱和式抓取引擎、按需建表、表名自愈、全局悬浮导航

---

## 🧠 Data Analyst Agent 2.0 架构

### 1. 记忆与自愈引擎 (Memory & Healing Engine)
*   **On-Demand Schema Loading**: 
    *   **Pruning**: 在数据库校验前，先根据问题进行相关性裁剪（Relevant Table Selection），仅保留当前查询必需的表定义。
    *   **Speed**: 避免了对百表规模知识库的全量扫描，将环境初始化时间从 $O(N)$ 降至 $O(1)$。
*   **Schema Healing & Mapping**:
    *   **Alias Discovery**: 当检测到 Schema 与物理库表名不一致时，通过模糊匹配（单复数、前缀后缀）寻找“物理替身”。
    *   **Memory Redirection**: 在内存中建立映射字典，后续 SQL 生成阶段自动将逻辑表名重定向为物理表名。

---

## 🏗️ 爬虫架构演进 (v6.6.5)

### 1. 饱和式抓取管线 (Saturation Queue Pipeline)
系统废弃了传统的 BFS 分层递归模式，转向**饱和式队列模式**以对齐高性能原生脚本：
*   **Continuity**: 采用单线程 `while` 队列逻辑。只要发现符合 `scope_prefix` 的链接，立刻入队，直至队列耗尽。
*   **WAF Safe**: 引入了物理级降速（Intelligent Throttling），并发限制为 1，确保抓取过程不被云端防火墙中断。
*   **Strict Scoping**: 直接应用 `startswith(Full_URL_Prefix)` 判定逻辑，消除协议与路径解析导致的断流。

---

## 🧩 核心流程演进

### 1. 饱和式抓取流程 (v6.6.5)
```
输入 Start URL 
    ↓
计算 Full URL Scope (含协议+域名+根路径)
    ↓
初始化饱和队列 (urls_to_visit)
    ↓
[循环抓取]
    ↓
html2text 提取 (锁定 content-wrapper)
    ↓
1:1 链接提取 (urljoin + prefix match)
    ↓
URL 路径映射文件名 (物理对齐)
    ↓
自动化元数据打标 (Mac xattr)
```


