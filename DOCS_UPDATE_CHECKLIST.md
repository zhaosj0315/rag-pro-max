# 📋 代码开发完成后文档更新执行清单

**用途**: 代码开发完成后，按此清单执行文档同步更新  
**原则**: 以代码为准，所有文档版本逻辑保持一致

---

## 🎯 执行步骤

### 1️⃣ 检查当前代码版本
```bash
# 查看当前版本
cat version.json | grep version

# 记录版本号，如: v2.4.7
```

### 2️⃣ 批量更新所有文档版本号
```bash
# 替换 OLD_VERSION 为实际的旧版本号，NEW_VERSION 为新版本号
# 例如: v2.4.6 → v2.4.7

for file in *.md; do
  sed -i '' 's/vOLD_VERSION/vNEW_VERSION/g' "$file"
  sed -i '' 's/版本.*vOLD_VERSION/版本**: vNEW_VERSION/g' "$file"
  sed -i '' 's/Version.*vOLD_VERSION/Version**: vNEW_VERSION/g' "$file"
done
```

### 3️⃣ 更新核心指标
```bash
# 更新README测试覆盖率徽章 (从version.json获取test_coverage)
sed -i '' 's/test%20coverage-[0-9.]*%25/test%20coverage-NEW_COVERAGE%25/g' README.md

# 更新TESTING.md测试结果
sed -i '' 's/OLD_TEST_RESULT/NEW_TEST_RESULT/g' TESTING.md
```

### 4️⃣ 更新CHANGELOG.md
在文件开头添加新版本记录：
```markdown
## vNEW_VERSION (YYYY-MM-DD) - 版本代号

### 🚀 新功能
- 功能描述1
- 功能描述2

### 🐛 修复
- 修复描述1
- 修复描述2

### 🔧 优化
- 优化描述1
- 优化描述2

---
```

### 5️⃣ 检查缺少版本标记的文档
```bash
# 检查哪些文档缺少版本标记
for file in *.md; do
  if ! grep -q "vNEW_VERSION" "$file"; then
    echo "需要手动更新: $file"
  fi
done
```

### 6️⃣ 手动添加版本标记到规范文档
对于开发规范类文档，手动添加版本标记：
```bash
# 在文档第2行插入版本信息
sed -i '' '2i\
**版本**: vNEW_VERSION  \
**更新日期**: YYYY-MM-DD\
' CONTRIBUTING.md DEVELOPMENT_CLEANUP_STANDARD.md DEVELOPMENT_STANDARD.md NON_ESSENTIAL_PUSH_STANDARD.md
```

### 7️⃣ 验证对齐完成
```bash
# 检查所有文档是否都包含新版本号
echo "=== 版本对齐检查 ==="
grep -l "vNEW_VERSION" *.md | wc -l
echo "总文档数:"
ls *.md | wc -l

# 两个数字应该相等
```

### 8️⃣ 提交并推送
```bash
# 提交所有更新
git add .
git commit -m "docs: 按文档管理规范对齐所有文档到 vNEW_VERSION

✅ 完成内容:
- XX个文档全部更新版本标记到 vNEW_VERSION
- 同步测试覆盖率到 XX% (XX/97)
- 完善 CHANGELOG 记录 [版本特性描述]
- 所有文档符合维护标准规范

🎯 核心特性:
- [特性1描述]
- [特性2描述]
- [特性3描述]"

# 推送到GitHub
git push origin main
```

### 9️⃣ 确认推送成功
```bash
# 检查推送状态
git status
git log --oneline -2
```

---

## 📋 必须更新的文档清单

### 🔥 核心文档 (每次必须同步)
- [ ] **version.json** - 版本号基准
- [ ] **README.md** - 版本徽章 + 测试覆盖率
- [ ] **CHANGELOG.md** - 新版本更新记录
- [ ] **USER_MANUAL.md** - 用户手册版本
- [ ] **TESTING.md** - 测试结果更新
- [ ] **API.md** - API文档版本
- [ ] **ARCHITECTURE.md** - 架构文档版本
- [ ] **DEPLOYMENT.md** - 部署指南版本
- [ ] **FAQ.md** - 常见问题版本
- [ ] **FIRST_TIME_GUIDE.md** - 首次使用指南

### 📄 辅助文档 (按需更新)
- [ ] **ANDROID_COMPATIBILITY_ANALYSIS.md** - Android兼容性
- [ ] **CONTRIBUTING.md** - 贡献指南
- [ ] **DEVELOPMENT_CLEANUP_STANDARD.md** - 开发清理标准
- [ ] **DEVELOPMENT_STANDARD.md** - 开发规范标准
- [ ] **DOCUMENTATION_MAINTENANCE_STANDARD.md** - 文档维护标准
- [ ] **NON_ESSENTIAL_PUSH_STANDARD.md** - 推送规范标准

---

## 🎯 快速执行模板

```bash
# 1. 获取新版本号
NEW_VERSION=$(cat version.json | grep '"version"' | cut -d'"' -f4)
echo "当前版本: v$NEW_VERSION"

# 2. 批量更新版本号 (替换OLD_VERSION)
for file in *.md; do
  sed -i '' "s/v2\.4\.[0-6]/v$NEW_VERSION/g" "$file"
done

# 3. 更新测试覆盖率 (从version.json获取)
COVERAGE=$(cat version.json | grep '"test_coverage"' | cut -d'"' -f4 | cut -d'/' -f1)
TOTAL=$(cat version.json | grep '"test_coverage"' | cut -d'"' -f4 | cut -d'/' -f2)
PERCENT=$(echo "scale=1; $COVERAGE * 100 / $TOTAL" | bc)
sed -i '' "s/test%20coverage-[0-9.]*%25/test%20coverage-${PERCENT}%25/g" README.md

# 4. 验证完成
echo "版本对齐文档数: $(grep -l "v$NEW_VERSION" *.md | wc -l)"
echo "总文档数: $(ls *.md | wc -l)"

# 5. 提交推送
git add . && git commit -m "docs: 对齐所有文档到 v$NEW_VERSION" && git push origin main
```

---

## ⚠️ 注意事项

1. **执行前备份**: 建议先创建分支备份
2. **版本号格式**: 确保版本号格式统一 (v2.4.x)
3. **测试覆盖率**: 从 version.json 获取准确数据
4. **CHANGELOG**: 手动编写，描述具体更新内容
5. **验证完整性**: 确保所有文档都包含新版本号

---

**使用说明**: 代码开发完成后，直接按此清单执行即可完成所有文档的版本对齐更新。
