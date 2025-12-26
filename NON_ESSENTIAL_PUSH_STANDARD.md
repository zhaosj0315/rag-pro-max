# 非必要不推送原则维护标准
**版本**: v2.6.1  
**更新日期**: 2025-12-19


## 🎯 核心原则
**本地保留所有，远程只推核心代码**

---

## 🔒 维护检查清单

### 📋 推送前必检项目

#### 1. .gitignore 文件检查
- [ ] **位置**: `/Users/zhaosj/Documents/rag-pro-max/.gitignore`
- [ ] **作用**: 自动防止私有文件推送
- [ ] **检查**: 确保包含所有私有文件类型

#### 2. 私有数据目录检查
```bash
# 检查这些目录是否被忽略
vector_db_storage/     # 用户知识库数据
chat_histories/        # 用户对话记录  
app_logs/             # 应用运行日志
temp_uploads/         # 临时上传文件
hf_cache/             # 模型缓存文件
exports/              # 导出的测试数据
```

#### 3. 临时文件检查
```bash
# 检查这些文件是否被忽略
crawler_state*.json   # 爬虫状态文件
*.tmp, *.temp        # 临时文件
.DS_Store            # 系统文件
__pycache__/         # Python缓存
*.pyc, *.pyo         # 编译文件
```

---

## 🛠️ 维护工具和命令

### 检查命令
```bash
# 1. 检查当前忽略状态
git status --ignored

# 2. 检查远程仓库文件
git ls-tree -r --name-only origin/main | grep -E "(vector_db|chat_histories|app_logs|temp_uploads|hf_cache|exports)"

# 3. 检查本地私有文件
find . -name "vector_db_storage" -o -name "chat_histories" -o -name "app_logs" -o -name "temp_uploads" -o -name "hf_cache" -o -name "exports"
```

### 清理命令
```bash
# 从远程删除误推送的文件
git rm -r --cached 文件名
git commit -m "clean: 删除误推送的私有文件"
git push origin 分支名
```

### 预防命令
```bash
# 推送前安全检查
./scripts/pre_push_safety_check.sh
```

---

## 📁 .gitignore 维护标准

### 当前 .gitignore 位置
**文件路径**: `/Users/zhaosj/Documents/rag-pro-max/.gitignore`

### 必须包含的规则
```gitignore
# ===== 运行时数据 (本地保留，远程忽略) =====
vector_db_storage/*
!vector_db_storage/.gitkeep
chat_histories/*  
!chat_histories/.gitkeep
temp_uploads/
app_logs/*
!app_logs/.gitkeep
hf_cache/*
!hf_cache/.gitkeep

# ===== 测试和临时文件 =====
exports/
test_*_output/
*_test_*.txt
*_test_*.json
refactor_backups/
PRODUCTION_RELEASE_REPORT_*.md
crawler_state*.json
*.tmp
*.temp

# ===== 系统和缓存文件 =====
.DS_Store
__pycache__/
*.pyc
*.pyo
*.pyd
```

---

## 🚨 违规检测和修复

### 自动检测脚本
**位置**: `scripts/check_push_compliance.sh`
```bash
#!/bin/bash
# 检查是否有违规文件将被推送
git diff --cached --name-only | grep -E "(vector_db_storage|chat_histories|app_logs|temp_uploads|hf_cache|exports|\.pyc$|__pycache__|\.log$|\.db$|\.sqlite|\.pkl|\.pickle|crawler_state\.json)"
```

### 修复流程
1. **发现违规**: 运行检测脚本
2. **立即停止**: 不要推送
3. **更新 .gitignore**: 添加遗漏的规则
4. **清理缓存**: `git rm -r --cached 违规文件`
5. **重新提交**: 提交清理后的版本

---

## 📊 合规性监控

### 定期检查 (每周)
- [ ] 检查 .gitignore 文件完整性
- [ ] 检查远程仓库是否有新的违规文件
- [ ] 检查所有分支的合规性

### 发布前检查 (每次发布)
- [ ] 运行 `scripts/pre_push_safety_check.sh`
- [ ] 确认远程仓库文件数量合理 (< 400个)
- [ ] 确认没有大文件 (> 1MB)

### 紧急修复 (发现违规时)
- [ ] 立即从远程删除违规文件
- [ ] 更新 .gitignore 防止再次发生
- [ ] 通知团队成员注意

---

## 🎯 维护责任

| 检查项目 | 频率 | 负责人 | 工具 |
|---------|------|--------|------|
| .gitignore 更新 | 每次新增文件类型 | 开发者 | 手动编辑 |
| 推送前检查 | 每次推送 | 提交者 | 自动脚本 |
| 远程合规检查 | 每周 | 项目维护者 | 检查脚本 |
| 违规修复 | 发现时立即 | 发现者 | 清理脚本 |

---

## ✅ 合规确认清单

推送前必须确认：
- [ ] .gitignore 文件已更新
- [ ] 运行了安全检查脚本
- [ ] 没有私有数据将被推送
- [ ] 远程仓库保持精简状态

**合规标志**: 所有检查项都通过 ✅

---

## 📞 维护联系

**问题报告**: 发现违规文件立即报告
**维护建议**: 持续改进 .gitignore 规则
**工具改进**: 优化自动检查脚本
