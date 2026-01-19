# RAG Pro Max v7.0.1 企业级系统架构文档

**版本**: v7.0.1 (Flagship Extended Edition)  
**更新日期**: 2026-01-19  
**核心特性**: Crawler Bottleneck Removal, Distributed Singleton Executors, Legacy Stubbing

---

## 🕷️ 网页抓取饱和式架构 (v7.0.1)

针对超大规模文档摄入，我们统一了全系统的抓取安全水位线：

### 1. 异步饱和抓取逻辑 (Async Saturation)
- **硬编码上限解锁**: 在 `AsyncWebCrawler.crawl_recursive` 逻辑中，将 `len(saved_files) < 2000` 提升至 `50000`。
- **内存队列管理**: 采用 `urls_to_visit` 集合进行 URL 去重与队列管理，确保在 5 万页规模下依然能保持 O(1) 级别的查询效率。
- **标准对齐**: 此次调整实现了「异步并发模式」与「同步递归模式」在物理上限上的完全统一（50,000 Pts）。

---

## 🛡️ 架构鲁棒性与兼容性层 (v7.0.0)
... (此处逻辑未变) ...
