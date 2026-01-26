# RAG Pro Max v9.5.37 企业级部署指南 (Search Revolution)

**版本**: v9.5.37  
**更新日期**: 2026-01-26  
**核心特性**: 暴力抓取、暂存区治理、零白屏交互

---

## 🛠️ 运维与资产维护

### 1. 环境自检 (Diagnostics)
在复杂的企业内网或代理环境下，若智能搜索失效，请运行诊断脚本：
```bash
# 真实模拟搜索逻辑，输出 HTML 源码与链接提取报告
python3 scripts/maintenance/debug_search_live.py
```
若该脚本返回 `探测到 0 个链接`，请检查防火墙是否拦截了对 `bing.com` 或 `duckduckgo.com` 的请求。



### 2. 维护脚本 (v6.7.0 重构路径)
所有维护动作应通过 `scripts/` 目录下的规范化路径执行：
- **全量材料维护**: `./scripts/cleanup_materials.sh`
- **知识库一致性诊断**: `python scripts/maintenance/diagnose_kb.py`
- **故障自动修复**: `python scripts/maintenance/fix_existing_kb.py`

---

## 🛡️ 安全加固

### 1. 权限管理
在多用户 Linux/macOS 环境下，必须确保日志目录可写：
```bash
chmod -R 777 app_logs/
```

### 2. 隐私脱敏
系统导出的全量资产包已自动对 API 密钥进行脱敏处理，但建议在生产环境下禁用 `DEBUG` 模式。

---

## 📑 开发者参考文档
- [📐 架构总纲](ARCHITECTURE.md)
- [💎 核心实现](CORE_FEATURE_IMPLEMENTATION.md)
- [📊 数据分析流程](DATA_ANALYSIS_WORKFLOW.md)
- [📝 文档维护标准](docs/standards/DOCUMENTATION_MAINTENANCE_STANDARD.md)