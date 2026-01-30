# RAG Pro Max v9.7.0 企业级部署指南 (Unified Governance)

**版本**: v9.7.0  
**更新日期**: 2026-01-30  
**核心特性**: 全域治理、全景日志、权限隔离

---

## 🛠️ 运维与资产维护

### 1. 权限配置 (Permission Config)
v9.7.0 引入了严格的权限隔离。部署后请立即检查 `config/users.json`，确保管理员账号拥有 `view_stats`, `manage_system_config` 等核心治理权限。
- **监控入口**: 普通用户无法访问监控面板，仅 Admin 可见。
- **调度控制**: 资源调度器已迁移至后台，需 Admin 权限操作。

### 2. 环境自检 (Diagnostics)
在复杂的企业内网或代理环境下，若智能搜索失效，请运行诊断脚本：
```bash
# 真实模拟搜索逻辑，输出 HTML 源码与链接提取报告
python3 scripts/maintenance/debug_search_live.py
```
若该脚本返回 `探测到 0 个链接`，请检查防火墙是否拦截了对 `bing.com` 或 `duckduckgo.com` 的请求。

### 2. macOS 预览功能依赖
系统使用 `qlmanage` 提供原生文件预览。请确保部署环境满足以下条件：
- **操作系统**: macOS 12.0+ (Monterey 或更高版本)
- **权限**: 运行 Streamlit 的终端需授予 "Accessibility" 或 "Automation" 权限（用于 AppleScript 置顶窗口）。
- **Headless 模式**: 若在无头服务器（Linux Server）部署，预览按钮将自动降级或仅显示路径复制功能。

### 3. 维护脚本 (Standard Maintenance)
所有维护动作应通过 `scripts/` 目录下的规范化路径执行：
- **代码全景审计**: `python scripts/maintenance/audit_codebase.py`
- **全量材料清理**: `./scripts/cleanup_materials.sh`
- **知识库一致性诊断**: `python scripts/maintenance/diagnose_kb.py`

---

## 🛡️ 安全加固

### 1. 权限管理
在多用户 Linux/macOS 环境下，必须确保日志目录可写：
```bash
chmod -R 777 app_logs/
```

### 2. 端口自愈
系统内置了 `8501` (App) 和 `8899` (WebSSH) 端口的自动清理逻辑。若遇到 `Address already in use` 错误，可以直接运行：
```bash
# 强制终止残留进程
lsof -ti:8501,8899 | xargs kill -9
```

### 3. 隐私脱敏
系统导出的全量资产包已自动对 API 密钥进行脱敏处理，但建议在生产环境下禁用 `DEBUG` 模式。

---

## 📑 开发者参考文档
- [📐 架构总纲](ARCHITECTURE.md)
- [💎 核心实现](CORE_FEATURE_IMPLEMENTATION.md)
- [📊 数据分析流程](DATA_ANALYSIS_WORKFLOW.md)
- [📝 文档维护标准](docs/standards/DOCUMENTATION_MAINTENANCE_STANDARD.md)
