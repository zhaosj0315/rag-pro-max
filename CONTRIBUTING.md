# 贡献指南 (Contributing Guide)

**版本**: v9.5.37 (Search Revolution Edition)
**更新日期**: 2026-01-26  
**架构标准**: 归一化并集摄入、单例并行执行、逻辑唯一性

## v9.5.37 核心架构标准 (New)

### 1. 智能搜索革命 (Smart Search Revolution)
- **Level 0 暴力探测**: 任何涉及网页搜索的模块，**必须** 采用 `requests` + `re` 的正则提取模式。严禁在探测阶段使用 `BeautifulSoup` 或 `Selenium` 等重型解析器。
- **重定向解壳**: 必须集成 `extract_real_url` 逻辑，在 HTTP 层面直接剥离 Bing/DDG 的跳转外壳，禁止跟随 302 跳转消耗带宽。
- **种子隔离**: 搜索引擎结果页 (SERP) 仅能作为 Level 0 种子，**绝对禁止** 将 SERP 页面本身作为文档内容存入 `content` 字段。

### 2. 暂存区审计规范 (Staging Audit)
- **伴生元数据**: 任何写入暂存区的操作，必须同步生成同名 `.meta` 文件（记录 Source/SyncTime）。
- **索引屏蔽 (Meta-Shielding)**: **严禁** 将 `.meta` 文件传入 `IndexBuilder` 或 `VectorStoreIndex`。文件扫描器必须包含 `if not f.endswith('.meta')` 过滤逻辑。

---

## v9.5.1 归一化摄入标准

### 1. 全能并集摄入 (Omni-Ingestion)
所有涉及非结构化源导入的功能**必须**遵循「暂存区 (Staging Area)」模式：
- **解耦交互**: 严禁在 UI 逻辑中直接修改 `uploaded_path`。
- **投递机制**: 必须调用 `sync_to_staging` 将材料投递至 `task_staging_dir` 物理桶。
- **数据库物料化**: 任何数据库查询结果必须通过 `DatabaseExporter` 先流式写入为 CSV 文件，再作为普通文件参与构建。

### 2. 存储配额豁免规范
- 任何执行磁盘空间校验的逻辑，必须显式排除 `admin` 角色。
- 严禁硬编码配额数值，必须从 `users.json` 实时获取 `storage_quota_mb` 字段。

---

## v9.0.0 开发标准

### 1. 逻辑唯一性原则 (Pure Logic Unification)
- 核心准则：**“全系统中业务逻辑只有一条物理路径”**。
- 严禁在子模块中重写已有的工具函数。
- 所有新功能必须直接集成至扁平化的 `apppro.py` 或核心 Service 层。

### 2. 双核联动准则 (Dual-Core Integration)
- **RAG 底座优先**: 任何处理流程必须确保不干扰全量 RAG 索引的构建。
- **插件化扩展**: 复杂逻辑计算（如数据分析、图谱推演）应作为高级选项挂载，通过 `enable_xxx` 标志位触发。

### 3. 并行执行安全 (Singleton Executors)
- **单例模式**: 必须通过 `src.utils.parallel_executor.get_global_executor()` 获取执行器。
- **防崩溃机制**: 禁止在嵌套闭包中直接实例化 `ParallelExecutor`，以防止 Streamlit 环境下的 `NameError`。

---

## 行为准则

为了营造一个开放和友好的环境，我们承诺使用友好和包容的语言，尊重不同的观点，并关注对社区最有利的事情。

## 如何贡献

### 报告 Bug
1. **检查现有 Issues**。
2. **使用最新版本**复现。
3. **提供详细信息**（环境、复现步骤、日志）。

### 提出新功能
1. **说明用例**：解释为什么需要这个功能。
2. **建议实现**：描述其如何融入 Omni-Ingestion 架构。

### 提交代码
1. **Fork & Branch**。
2. **编写代码**：遵循 PEP 8 和本项目单例执行规范。
3. **出厂测试**：执行 `./scripts/test.sh`。
4. **提交 PR**。

## 代码规范

### 最小化原则
**只写必要的代码**：
```python
# 好的：简洁明了
filtered = [x for x in items if x > 0]

# 避免：过度复杂
filtered = []
for item in items:
    if item > 0:
        filtered.append(item)
```

### 命名规范
- **变量/函数**: `snake_case`
- **类**: `PascalCase`
- **常量**: `UPPER_CASE`

## 提交规范

### Commit Message 格式
```
<type>(<scope>): <subject>
```
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `refactor`: 重构
- `test`: 测试相关

## 测试要求

**所有代码必须通过出厂测试**:
```bash
./scripts/test.sh
```
测试内容包含：环境检查、配置文件、核心模块、单例执行器安全性、双核联动稳定性。

---

**感谢你的贡献！** 🎉
每一个贡献，无论大小，都让 RAG Pro Max 变得更好。
