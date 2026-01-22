# RAG Pro Max 性能极致优化与硬件加速白皮书

**版本**: v1.0
**关键指标**: GPU 加速、5万页饱和抓取、动态内存清理

## 1. 硬件级加速 (Hardware Deep Integration)
- **Apple Silicon Optimized**: 针对 M4 Max (MPS) 提供原生 GPU 向量化加速。
- **Dynamic Batching**: 根据系统剩余显存自动调整 Embedding Batch Size（最高 2048），在不撑爆显存的前提下压榨最大算力。

## 2. 爬虫调度算法 (Saturation Crawl Algorithm)
- **指数级递归 (Exponential Growth)**: 采用 $n^{depth}$ 的配额分配，支持 5+25 等深度扩散模型。
- **饱和队列**: 实现异步并发爬虫队列，支持单次任务最高 50,000 页的饱和式抓取，具备自动重试与反爬保护机制。

## 3. 内存与资源调度 (Resource Throttling)
- **物理暂存优化**: 通过 `Staging Area` 避免大文件在内存中积压，采用“分片读取 -> 及时释放”策略。
- **自愈式清理**: 集成 `gc` 深度回收与显存手动清空逻辑，确保系统在高并发构建后能迅速回归低负载状态。
