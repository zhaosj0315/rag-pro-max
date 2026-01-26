# RAG Pro Max 系统鲁棒性与自愈策略规范

**状态**: 生效中
**核心指标**: 7x24h 稳定性、现场恢复、静默修复

## 1. 物理目录自愈 (Staging Auto-Heal)
- **发现**: 页面刷新或系统清理可能导致 `task_staging_dir` 物理路径缺失。
- **自愈**: 系统在执行 `os.listdir` 前执行 `os.path.exists` 校验，若缺失则静默重建目录，并在终端输出 `⚠️ 暂存目录丢失，已自动重建` 警告，防止程序崩溃。

## 2. 知识库加载保护 (Load Failsafe)
- **索引完整性**: 针对 `docstore.json` 缺失导致的加载错误，引入“自愈引导”，尝试从 `raw_sources/` 重新恢复索引元数据。
- **模型回退**: 当 GPU 驱动异常或显存溢出时，系统自动回退至 CPU 离线 Embedding 模式，确保核心问答功能“永远在线”。

## 3. 大数据流式导出防护 (Streaming Export Safety)
- **OOM 防御**: `DatabaseExporter` 严禁一次性将全表读入内存。必须强制使用 `pd.read_sql(..., chunksize=10000)` 分块读取策略。
- **流式写入**: 采用 `mode='a'` 追加模式，将 CSV 数据流式写入磁盘，确保内存峰值恒定，不受数据量级（如千万行）影响。

## 4. 现场恢复机制 (Context Restoration)
- **URL 参数持久化**: 通过 `st.query_params` 将当前的 `kb_id` 和 `session_id` 实时映射至浏览器地址栏。
- **刷新不掉线**: 用户刷新浏览器后，系统自动从 URL 恢复当前的对话现场与知识库挂载状态。
