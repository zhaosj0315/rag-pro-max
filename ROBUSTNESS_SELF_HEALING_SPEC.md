# RAG Pro Max 系统鲁棒性与自愈策略规范

**状态**: v9.8.0 生效中
**核心指标**: 7x24h 稳定性、现场恢复、静默修复

## 6. 数据分析 JIT 自愈 (Data Analysis JIT Rescue)
- **发现**: 当用户查询触发 SQL 执行时，检测到目标表 (Virtual Table) 在物理数据库中为空或不存在。
- **自愈**: 拦截 SQL 执行错误，触发 `_ensure_sandbox_ready` 机制。系统自动根据 Schema 定义和当前 Query 上下文，调用 LLM 现场生成 30+ 条模拟数据并注入数据库，随后重试 SQL 查询，实现对用户的“无感修复”。

## 7. 隐式对话路由自愈 (Implicit Chat Routing)
- **发现**: 用户在未选择任何知识库（或 Session 初始化未完成）的情况下直接在输入框提问。
- **自愈**: 系统自动捕获该异常状态，将当前会话降级为 **Pure Chat** 模式。同时，自动生成用户隔离的 Session ID 并同步侧边栏 UI，确保用户的提问不会丢失，且能被无缝归档。

## 1. 物理目录自愈 (Staging Auto-Heal)
- **发现**: 页面刷新或系统清理可能导致 `task_staging_dir` 物理路径缺失。
- **自愈**: 系统在执行 `os.listdir` 或写入文件前，执行 `os.path.exists` 校验，若缺失则静默重建目录，防止程序因 `FileNotFoundError` 崩溃。

## 2. 搜索链路自愈 (Violent Discovery)
- **反脆弱**: 针对搜索引擎（Bing/DDG）的结构混淆与 WAF 拦截，v9.5.37 引入了“暴力探测”降维打击。
- **正则兜底**: 当 HTML 解析器失效时，自动切换至正则表达式模式，直接从原始字节流中提取链接，确保抓取任务“永远有产出”。

## 3. 服务端口自愈 (Port Self-Healing)
- **僵尸进程清理**: 启动时自动检测 `8501` (App) 和 `8899` (WebSSH) 端口占用。
- **主动熔断**: 集成 `lsof -ti | xargs kill -9` 逻辑，强制终止残留的后台进程，确保新服务能成功绑定端口。

## 4. 大数据流式导出防护 (Streaming Export Safety)
- **OOM 防御**: `DatabaseExporter` 严禁一次性将全表读入内存。必须强制使用 `pd.read_sql(..., chunksize=10000)` 分块读取策略。
- **流式写入**: 采用 `mode='a'` 追加模式，将 CSV 数据流式写入磁盘，确保内存峰值恒定。

## 5. 现场恢复机制 (Context Restoration)
- **URL 参数持久化**: 通过 `st.query_params` 将当前的 `kb_id` 和 `session_id` 实时映射至浏览器地址栏。
- **刷新不掉线**: 用户刷新浏览器后，系统自动从 URL 恢复当前的对话现场与知识库挂载状态。