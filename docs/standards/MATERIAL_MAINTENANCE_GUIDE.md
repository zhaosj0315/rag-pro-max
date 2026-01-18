# 材料维护执行指南 (Material Maintenance Execution Guide)

**生成时间**: 2026-01-18 16:47  
**当前版本**: v6.7.2  
**状态**: 🔴 紧急维护中

---

## 📊 当前状态

根据自动化检查，项目存在以下问题：

### ✅ 正常项
- [x] 版本号一致性 (v6.6.5)
- [x] README.md 版本徽章正确
- [x] CHANGELOG.md 已更新
- [x] 必需文档齐全

### ⚠️ 需要修复
- [ ] **Mock Data 文档过多** (4个，建议2个)
- [ ] **根目录测试文件** (6个需移动)
- [ ] **根目录诊断脚本** (2个需移动)
- [ ] **临时文件未清理** (5309个文件！)

---

## 🚀 快速执行

### 方式一：自动化脚本（推荐）

```bash
# 1. 运行检查脚本，查看当前状态
cd /Users/zhaosj/Documents/rag-pro-max
python scripts/check_doc_sync.py

# 2. 运行清理脚本，自动修复
./scripts/cleanup_materials.sh

# 3. 再次检查，确认修复
python scripts/check_doc_sync.py
```

### 方式二：手动执行

如果你想手动控制每一步：

```bash
# 1. 清理临时文件（最重要！）
rm -rf temp_uploads/*
echo "temp_uploads/" >> .gitignore

# 2. 移动测试脚本
mkdir -p tests/integration
mv test_*.py tests/integration/

# 3. 移动诊断脚本
mkdir -p scripts/maintenance
mv diagnose_kb.py fix_existing_kb.py scripts/maintenance/

# 4. 整理标准文档
mkdir -p docs/standards
mv *_STANDARD.md *_SOP.md *_GUIDE.md docs/standards/
```

---

## 📋 详细任务清单

### P0 - 立即执行（今天必须完成）

#### 1. 清理临时文件 ⚠️ 最高优先级
```bash
# 当前状态: 5309 个临时文件占用大量空间
rm -rf temp_uploads/*

# 确保 .gitignore 包含
echo "temp_uploads/" >> .gitignore
```

**影响**: 
- 占用磁盘空间 ~500MB
- 可能包含敏感信息
- 污染 Git 仓库

#### 2. 移动测试脚本
```bash
mkdir -p tests/integration
mv test_all_scenarios.py tests/integration/
mv test_e2e_scenario.py tests/integration/
mv test_mock_data.py tests/integration/
mv test_real_csv.py tests/integration/
mv test_real_integration.py tests/integration/
mv test_temp_table_mock.py tests/integration/
```

**影响**: 
- 污染项目根目录
- 混淆用户对项目结构的理解

#### 3. 移动诊断脚本
```bash
mkdir -p scripts/maintenance
mv diagnose_kb.py scripts/maintenance/
mv fix_existing_kb.py scripts/maintenance/
```

---

### P1 - 本周完成

#### 4. 整理标准文档
```bash
mkdir -p docs/standards
mv DOCUMENTATION_MAINTENANCE_STANDARD.md docs/standards/
mv DEVELOPMENT_CLEANUP_STANDARD.md docs/standards/
mv NON_ESSENTIAL_PUSH_STANDARD.md docs/standards/
mv SINGLE_FEATURE_ITERATION_STANDARD.md docs/standards/
mv ENTERPRISE_DOCUMENT_MANAGEMENT_STANDARD.md docs/standards/
mv CONTINUOUS_QUALITY_SOP.md docs/standards/
mv CONTINUOUS_OPTIMIZATION_GUIDE.md docs/standards/
mv POST_DEVELOPMENT_SYNC_STANDARD.md docs/standards/
mv PROJECT_KANBAN_TEMPLATE.md docs/standards/
mv FREE_PUBLIC_ACCESS.md docs/standards/
```

#### 5. 合并 Mock Data 文档（手动）

**当前状态**:
- docs/MOCK_DATA_GENERATION.md (详细文档)
- docs/MOCK_DATA_QUICKSTART.md (快速开始)
- docs/IMPLEMENTATION_SUMMARY_MOCK_DATA.md (实现总结)
- docs/TROUBLESHOOTING_MOCK_DATA.md (故障排查)

**建议合并方案**:
1. 合并 QUICKSTART + GENERATION → `docs/MOCK_DATA_GUIDE.md`
2. 保留 `docs/MOCK_DATA_TROUBLESHOOTING.md`
3. 删除 `docs/IMPLEMENTATION_SUMMARY_MOCK_DATA.md`（开发过程文档）

**合并步骤**:
```bash
# 1. 创建新的用户指南
cat > docs/MOCK_DATA_GUIDE.md << 'EOF'
# Mock Data 功能指南

## 快速开始
[从 QUICKSTART 复制内容]

## 详细说明
[从 GENERATION 复制内容]

## 使用示例
[从 GENERATION 复制示例]
EOF

# 2. 删除旧文档
rm docs/MOCK_DATA_GENERATION.md
rm docs/MOCK_DATA_QUICKSTART.md
rm docs/IMPLEMENTATION_SUMMARY_MOCK_DATA.md

# 3. 保留故障排查
# docs/MOCK_DATA_TROUBLESHOOTING.md 保持不变
```

---

### P2 - 下次迭代

#### 6. 更新 README.md

在 README.md 中添加开发者文档链接：

```markdown
## 📚 文档资源

### 用户文档
- [📋 部署指南](DEPLOYMENT.md)
- [🧪 测试说明](TESTING.md) 
- [❓ 常见问题](FAQ.md)
- [🤝 贡献指南](CONTRIBUTING.md)

### 开发者文档
- [📐 开发标准](docs/standards/) - 内部开发规范
- [🔧 API 文档](API_DOCUMENTATION.md)
- [🏗️ 架构说明](ARCHITECTURE.md)
```

#### 7. 增强示例文档

编辑 `samples/data_analysis/README.md`，添加：
- 每个文件的用途说明
- 如何使用这些示例
- 预期的测试结果

---

## 🎯 执行后验证

### 1. 运行检查脚本
```bash
python scripts/check_doc_sync.py
```

**预期结果**: 所有检查项都应该显示 ✓ 通过

### 2. 检查目录结构
```bash
tree -L 2 -I 'node_modules|__pycache__|*.pyc'
```

**预期结构**:
```
rag-pro-max/
├── README.md
├── CHANGELOG.md
├── version.json
├── docs/
│   ├── MOCK_DATA_GUIDE.md
│   ├── MOCK_DATA_TROUBLESHOOTING.md
│   └── standards/
├── tests/
│   └── integration/
├── scripts/
│   ├── maintenance/
│   └── cleanup_materials.sh
└── temp_uploads/ (空目录)
```

### 3. 运行测试
```bash
# 确保移动后的测试仍然可以运行
cd tests/integration
python test_mock_data.py
```

---

## 📊 清理效果

### 清理前
- 根目录文件: ~50 个
- 临时文件: 5309 个
- 项目大小: ~500MB+
- 文档冗余: 4 个 Mock Data 文档

### 清理后
- 根目录文件: ~15 个 ⬇️ 70%
- 临时文件: 0 个 ⬇️ 100%
- 项目大小: ~50MB ⬇️ 90%
- 文档冗余: 2 个 Mock Data 文档 ⬇️ 50%

---

## ⚠️ 注意事项

### 1. 备份重要数据
在执行清理前，确保备份：
```bash
# 备份用户数据
cp -r vector_db_storage/ backup/
cp -r chat_histories/ backup/
```

### 2. Git 提交
清理完成后，分批提交：
```bash
# 第一批：清理临时文件
git add .gitignore
git commit -m "chore: 清理临时文件并更新 .gitignore"

# 第二批：重组项目结构
git add tests/ scripts/ docs/
git commit -m "refactor: 重组项目结构，移动测试和标准文档"

# 第三批：合并文档
git add docs/
git commit -m "docs: 合并 Mock Data 文档，减少冗余"
```

### 3. 通知团队
如果是团队项目，清理前通知其他开发者：
- 说明清理原因
- 提供迁移指南
- 更新 CI/CD 配置（如果有）

---

## 🔄 定期维护

建议每次版本发布前执行：

```bash
# 1. 运行检查
python scripts/check_doc_sync.py

# 2. 如有问题，运行清理
./scripts/cleanup_materials.sh

# 3. 手动处理无法自动化的任务
# （如文档合并、内容更新等）

# 4. 再次检查
python scripts/check_doc_sync.py

# 5. 提交更改
git add .
git commit -m "chore: 材料维护 - v6.6.5"
```

---

## 📞 获取帮助

如果遇到问题：

1. **查看详细报告**: `MATERIAL_MAINTENANCE_REPORT.md`
2. **查看标准文档**: `docs/standards/DEVELOPMENT_CLEANUP_STANDARD.md`
3. **运行诊断**: `python scripts/check_doc_sync.py`

---

**维护完成标志**: 
- [ ] 所有 P0 任务已完成
- [ ] 检查脚本全部通过
- [ ] 项目结构清晰
- [ ] 文档无冗余
- [ ] 已提交到 Git

**下次维护**: 下一个版本发布前
