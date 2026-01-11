# RAG Pro Max 开发规范标准
**版本**: v4.3.0  
**更新日期**: 2026-01-11  


## 🎯 核心原则
**标准化开发 - 确保代码质量、文档同步、安全合规的开发流程**

---

## 📋 并发编程准则 (v4.3.0 新增)
针对 v4.3.0 的架构调整，开发者必须遵循以下并发选择逻辑：
1. **CPU 密集型任务**: 使用 `ProcessPoolExecutor`。注意 worker 函数必须在模块顶层以支持 pickle。
2. **I/O 密集型/混合型任务**: 在 macOS (Darwin) 下必须使用 `ThreadPoolExecutor`，以避免 Streamlit 环境下的进程分叉崩溃。
3. **Streamlit 安全**: 禁止在子进程中直接访问 `st.session_state` 或执行 `st.*` 命令。

---

## 📋 开发流程规范

### 🚀 开发启动阶段

#### 1. 环境准备
```bash
# 检查开发环境
python --version  # 必须 Python 3.9+
```

#### 2. 分支管理
...
### 📝 文档同步规范

#### 需要同步的文档
- README.md          # 新功能说明
- CHANGELOG.md       # 版本变更记录
- ARCHITECTURE.md    # 架构演进说明
- USER_MANUAL.md     # 使用说明更新
- DEPLOYMENT.md      # 部署环境变化
```

### 🧪 测试规范
- ✅ **测试覆盖率**: 核心逻辑要求 100% 覆盖，UI 组件要求 80% 覆盖。
- ✅ **macOS 验证**: 涉及文件系统或 OCR 的功能必须在 macOS 环境下验证 native 能力。

---

## 🔒 安全开发规范
...
## 📊 版本管理规范

### 版本号规范
```json
// version.json
{
    "version": "4.3.0",
    "build_number": "20260111.10",
    "status": "stable"
}
```

#### 版本号规则
- **主版本号**: 重大架构变更 (2.x.x)
- **次版本号**: 新功能添加 (x.4.x)  
- **修订版本号**: Bug修复 (x.x.4)

### 提交规范
```bash
# 提交信息格式
<类型>: <简要描述>

<详细描述>
- 变更点1
- 变更点2

# 类型说明
feat:     新功能
fix:      Bug修复
docs:     文档更新
style:    代码格式调整
refactor: 代码重构
test:     测试相关
chore:    构建/工具变更
```

#### 提交示例
```bash
git commit -m "feat: 添加PDF批量处理功能

🚀 新增功能
- 支持文件夹批量上传PDF
- 自动OCR识别扫描版PDF
- 进度条显示处理状态

🔧 技术改进
- 优化内存使用
- 添加错误重试机制

✅ 测试覆盖: 92%"
```

---

## 🛠️ 开发工具规范

### 必备开发工具
```bash
# 代码格式化
pip install black isort

# 代码检查
pip install flake8 mypy

# 测试工具
pip install pytest pytest-cov

# 文档工具
pip install sphinx
```

### 开发脚本使用
```bash
# 文档同步检查
python scripts/check_documentation_sync.py

# 推送前安全检查
./scripts/pre_push_safety_check.sh

# 开发材料清理
./scripts/cleanup_development_materials.sh

# 清理完整性检查
python scripts/check_cleanup_completeness.py
```

### IDE配置建议
```json
// .vscode/settings.json
{
    "python.defaultInterpreter": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true
}
```

---

## 📋 开发检查清单

### 功能开发完成检查
- [ ] 代码符合PEP 8规范
- [ ] 添加了必要的注释和文档字符串
- [ ] 通过所有单元测试
- [ ] 更新了相关文档
- [ ] 添加了使用示例
- [ ] 处理了异常情况
- [ ] 考虑了性能影响
- [ ] 遵循了安全规范

### 提交前检查
- [ ] 运行了完整测试套件
- [ ] 检查了文档同步状态
- [ ] 验证了代码质量
- [ ] 确认了提交信息格式
- [ ] 检查了敏感信息泄露

### 发布前检查
- [ ] 更新了版本号
- [ ] 更新了CHANGELOG.md
- [ ] 运行了推送前安全检查
- [ ] 清理了开发过程材料
- [ ] 验证了应用可正常启动

---

## 🎯 质量标准

### 代码质量指标
| 指标 | 要求 | 检查方式 |
|------|------|----------|
| 测试覆盖率 | ≥85% | pytest-cov |
| 代码规范 | PEP 8 | flake8 |
| 类型检查 | 无错误 | mypy |
| 文档同步 | 100% | 自动检查脚本 |
| 安全检查 | 通过 | 推送前检查 |

### 性能标准
- ✅ **启动时间**: ≤30秒
- ✅ **内存使用**: ≤4GB
- ✅ **响应时间**: ≤3秒
- ✅ **并发处理**: 支持多用户

### 用户体验标准
- ✅ **界面友好**: 直观易用
- ✅ **错误处理**: 友好的错误提示
- ✅ **文档完整**: 完整的使用指南
- ✅ **功能稳定**: 核心功能稳定可靠

---

## 🔄 持续改进

### 定期评估
- **每周**: 代码质量检查
- **每月**: 性能指标评估
- **每季度**: 开发流程优化

### 改进机制
- 📊 **数据驱动**: 基于指标数据改进
- 🔄 **迭代优化**: 持续优化开发流程
- 📝 **经验总结**: 记录最佳实践
- 🤝 **团队协作**: 分享开发经验

---

## 📞 支持资源

### 开发文档
- [架构文档](ARCHITECTURE.md)
- [API文档](API_DOCUMENTATION.md)
- [测试指南](TESTING.md)
- [部署指南](DEPLOYMENT.md)

### 维护标准
- [文档维护标准](DOCUMENTATION_MAINTENANCE_STANDARD.md)
- [推送规范](NON_ESSENTIAL_PUSH_STANDARD.md)
- [开发清理标准](DEVELOPMENT_CLEANUP_STANDARD.md)

### 自动化工具
- `scripts/check_documentation_sync.py`
- `scripts/pre_push_safety_check.sh`
- `scripts/cleanup_development_materials.sh`
- `scripts/check_cleanup_completeness.py`

**🎯 目标: 建立高效、安全、标准化的开发流程！**
