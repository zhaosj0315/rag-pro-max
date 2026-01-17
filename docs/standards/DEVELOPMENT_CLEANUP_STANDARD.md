# 全局代码质量与重构标准 (Global Code Quality & Refactoring Standard)

**版本**: v6.0.0 (Architect Edition)  
**更新日期**: 2026-01-16  
**适用范围**: 所有代码提交、重构任务及清理工作

---

## 🛡️ 核心法则 (Rules of Engagement)

本项目的代码维护遵循**"外科手术式"**原则：稳健、精准、零副作用。任何操作必须严格遵守以下三大铁律，违反任何一条均视为未完成任务。

### 1. 零回归 (Zero Regression / 100% Compatibility)
*   **定义**: 重构后的代码在**输入参数、输出结果、异常抛出类型、副作用（如日志、DB写入）**上必须与原代码保持完全一致。
*   **红线**: 禁止为了"代码优美"而改变任何外部行为。如果不确定行为是否一致，**禁止修改**。

### 2. 黑盒原则 (Black Box Principle)
*   **定义**: 外部调用者（Importer / Caller）不应感知到内部实现的任何变化。
*   **操作**: 
    *   保持函数签名（Signature）不变。
    *   保持模块导出（Exports）不变。
    *   私有化重构：新逻辑应封装在内部，对外暴露的接口仅仅是代理调用。

### 3. 防御性编程 (Defensive Programming)
*   **定义**: 面对不确定的依赖关系（如反射调用、动态导入），**宁可保留也不误删**。
*   **操作**: 
    *   如果不确定某段代码是否被引用，使用 `# TODO: [Review] Potential dead code, pending audit` 标记，而不是直接删除。
    *   保留"过时"的接口作为 Wrapper 调用新接口，并标记 `@deprecated`，而不是直接移除。

---

## 🧹 代码清理标准 (Code Cleanup Standard)

### 1. 识别并清理过程性代码
**目标**: 移除开发过程中产生的中间态逻辑。

| 类型 | 特征 | 处理方式 |
| :--- | :--- | :--- |
| **版本后缀函数** | `func_v1`, `func_old`, `_backup_2025` | **删除**。确认新版 `func` 已完全接管逻辑且测试通过后，彻底移除旧版。 |
| **临时调试代码** | `print("DEBUG: here")`, `if 1==1: # temporary bypass` | **删除**。所有非结构化日志（非 `logger` 调用）必须移除。 |
| **废弃的特性开关** | `if Feature_X_Enabled:` (Feature X 已全量上线) | **固化**。移除判断逻辑，直接保留 `True` 分支的代码，删除 `False` 分支。 |
| **死代码 (Dead Code)** | IDE 提示 "Unreachable code" 或 0 引用（需谨慎） | **删除前确认**。必须全局搜索字符串（grep）以防反射调用。无法确认时保留并注释。 |

### 2. 清理废弃材料 (Asset Cleanup)
*(保留原 v5.5.8 的文件清理清单，作为本标准的一部分)*

*   **内部文档**: 删除 `PHASE_*.md`, `*_STRATEGY.md` 等过程性文档。
*   **临时脚本**: 删除 `tools/debug_*.py`, `test_temp_*.py`。
*   **历史遗留**: 删除 `rag` (旧启动脚本), `kbllama`。

---

## 🏗️ 重构与优化协议 (Refactoring Protocol)

针对逻辑设计粗糙或复杂度过高的模块，必须按以下步骤执行。

### 1. 准备阶段
*   **理解上下文**: 阅读该模块所有相关测试。如果有测试缺失，**先补全测试，再开始重构**。
*   **锁定行为**: 确保当前测试全部通过 (`pytest tests/target_module.py`)。

### 2. 执行阶段 (对比模式)
在提交记录或 Pull Request 中，必须清晰展示优化逻辑。

**Case 1: 逻辑简化**
*   **Before**:
    ```python
    # 过程性冗余：手动过滤
    result = []
    for item in items:
        if item.is_valid():
            result.append(item)
    return result
    ```
*   **After**:
    ```python
    # 优化点：使用列表推导式，提升可读性
    return [item for item in items if item.is_valid()]
    ```

**Case 2: 消除硬编码**
*   **Before**:
    ```python
    path = "/Users/zhaosj/Documents/rag-pro-max/data"
    ```
*   **After**:
    ```python
    # 优化点：使用项目配置路径，增强移植性
    from src.config import SETTINGS
    path = SETTINGS.DATA_DIR
    ```

### 3. 验证阶段
*   **单元测试**: 必须 100% 通过。
*   **集成测试**: 运行相关业务流程的端到端测试。
*   **静态检查**: 运行 `pylint` / `mypy` 确保无新引入的类型错误。

---

## ⚠️ 风险评估与应对 (Risk Management)

在执行任何变更前，必须进行风险自评。

| 风险等级 | 场景 | 应对措施 |
| :--- | :--- | :--- |
| **高危 (Critical)** | 修改核心引擎 (`rag_engine.py`), 认证模块 (`auth/`), 文件读写 | 1. 必须有覆盖率 >90% 的测试。<br>2. 必须保留旧逻辑快照（注释掉）至少一个版本。<br>3. 必须人工复核。 |
| **中等 (Medium)** | UI 调整 (`apppro.py`), 辅助工具类 | 1. 本地运行验证。<br>2. 检查 UI 布局无崩坏。 |
| **低 (Low)** | 删除未引用的 `.md` 文件, 修正错别字 | 直接执行。 |

---

## 📝 必须保留的核心文件清单 (Whitelist)

**原则**: 除了以下核心资产，其他未被引用的文件均在潜在清理范围内。

1.  **源码**: `src/` (含 `__init__.py`)
2.  **配置**: `config/*.json` (生产环境配置)
3.  **测试**: `tests/` (作为回归基准)
4.  **文档**: `README.md`, `USER_MANUAL.md`, `API_DOCUMENTATION.md`, `CHANGELOG.md`
5.  **标准**: `DEVELOPMENT_CLEANUP_STANDARD.md` (本文档), `CONTINUOUS_QUALITY_SOP.md`
6.  **环境**: `requirements.txt`, `Dockerfile`, `docker-compose.yml`

---

## 🚀 执行工具 (Tooling)

*   **清理脚本**: 使用 `./scripts/cleanup_development_materials.sh` 进行文件级清理。
*   **依赖检查**: 使用 `pip-audit` 检查安全风险。
*   **死代码扫描**: 使用 `vulture` (需配置白名单) 辅助发现死代码。

---

**结语**:  
代码质量不是一蹴而就的，而是通过每一次遵循本标准的"微创手术"积累而来的。  
**Keep it Clean, Keep it Safe.**