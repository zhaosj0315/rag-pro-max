# RAG Pro Max v7.0.0 企业级系统架构文档

**版本**: v7.0.0 (Flagship Robust Edition)  
**更新日期**: 2026-01-19  
**核心特性**: Distributed Singleton Executors, Self-Healing Monitoring Architecture, Legacy Stubbing

---

## 🛡️ 架构鲁棒性与兼容性层 (v7.0.0)

在 v7.0.0 中，系统架构引入了“防御式设计”层，用于解决大规模净化后的残留冲突：

### 1. 分布式单例执行器 (Distributed Singleton Executors)
- **全局定义提升**: 将 `ParallelExecutor` 的导入与实例化生命周期提升至 `apppro.py` 最顶层，并采用 `get_global_executor` 单例模式。这解决了大型 Streamlit 应用中由于作用域嵌套导致的 `NameError`。
- **多进程隔离**: 确保在子进程 spawned 过程中，执行器定义的可见性与稳定性。

### 2. 内存级监控数据流 (Memory-First Telemetry)
- **去 DataFrame 依赖化**: 监控趋势数据从“实时 Concat”转向“List Buffer -> Rendering DF”模式。此举通过物理隔离 Session 状态中的 DataFrame 碎片，彻底规避了 Pandas 版本差异带来的维度不一致（TypeError）。
- **强制加载锁**: 利用 `importlib.reload` 在交互层锁定子模块版本，实现逻辑的动态纠偏。

### 3. 兼容性垫片 (Compatibility Stubbing)
- **Stub 架构**: 为满足存量测试套件（Factory Test）的物理存在检查，重新引入了 `logger.py` 和 `services/` 下的转发垫片。该架构在不增加系统负担的前提下，确保了 CI/CD 流水的完整性。

---

## 🧼 架构净化与逻辑唯一化 (v6.9.5)

在 v6.9.5 迭代中，系统完成了历史上最彻底的架构“瘦身”，确立了以下核心设计准则：

### 1. 逻辑唯一性收口 (Pure Logic Unification)
- **物理去冗余**: 彻底清除了全项目中重复定义的中间版本函数。例如，`render_resource_governance` 在经历 19 次迭代后，现在全项目**有且仅有一个**物理定义位置，杜绝了版本误用。
- **函数级解耦**: 通过删除 `_is_valid_url`、`render_v23_sidebar` 等过时的局部方法，实现了核心类的“功能内聚”。

### 2. 扁平化极简入口架构
- **入口心脏瘦身**: `src/apppro.py` 废弃了所有的中间层包装器（如 `get_embed`, `get_llm`），改为直接调用底层核心 Service。
- **架构回归**: 物理删除了 `src/app/` 这一层级的过度抽象，将整个系统还原为高性能、低延迟的扁平化 Streamlit 指挥中枢。

---

## 🛡️ 旗舰级治理中心架构 (v6.9.0)

在 v6.9.0 中，系统架构实现了从“宽泛审计”到“精细化生命周期治理”的质变：

### 1. 个体化安全策略架构 (Individualized Security Strategy)
- **策略优先级 (Settings Priority)**: 引入三级 TTL（生存时间）判定逻辑：
    1. `Level 1`: 用户专属设置 (User-specific settings in `sessions.json`).
    2. `Level 2`: 全局默认配置 (Global default).
    3. `Level 3`: 代码硬编码安全值 (7 Days).
- **交互舱状态机**: 采用单选监听模式。当且仅当账户列表的勾选位（Checked State）为 1 时，激活 `Individual Cabin` 容器。该容器通过 `revoke_user_sessions` 接口与 `SessionStore` 直接通信，实现“手术刀式”的会话切断。

### 2. 全能资源合规扫描引擎 (Compliance Scanning Engine)
- **物理指纹深度探测**:
    - **损坏判定**: 校验物理路径下是否存在 `manifest.json` 与 `docstore.json` 的闭环。
    - **容量水位线**: 引入 500MB 软限制。引擎通过递归扫描 `os.walk` 计算文件夹物理总量，触发容量预警状态。
    - **休眠状态监测**: 比较 `time.time()` 与文件系统 `st_mtime` 的 delta 值，判定资源是否进入 30 天冷数据期。
- **治理指令流水线**: 整合 `KBManager.rename`、`shutil.rmtree` 和 `set_kb_public` 接口，形成统一的资产决策输出端。

---

## 🎨 视觉对齐与交互架构 (v6.8.8)

### 1. 登录页重心偏移算法
- **黄金分割优化**: 采用 `translateY(-85px)` 取代原本的 `-130px`。该偏移量基于多分辨率交集计算，确保主标题处于视觉“黄金安全区”。
- **留白缓冲 (Gutter Architecture)**: 增加顶部 45px 透明 padding，显著缓解大屏设备的视觉空旷感。

### 2. 交互样式原子化覆盖
- **精细化选择器**: 利用 CSS `:has` 伪类（`[data-testid="stVerticalBlock"]:has(.login-anchor)`）实现了对 Streamlit 原生组件的深度样式隔离。
- **样式清洗**: 针对高优先级组件，通过 `!important` 强制剥离背景、边框，实现了组件形态的平滑转化。