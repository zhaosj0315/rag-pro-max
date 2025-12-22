# 📋 代码开发完成后完整准备工作执行清单

**用途**: 代码开发完成后，按此清单执行所有前置准备工作  
**原则**: 以代码为准，保障各个环节逻辑统一一致  
**范围**: 文档对齐 + 测试更新 + .gitignore对齐 + 推送准备

---

## 🎯 完整执行步骤

### 1️⃣ 检查当前代码版本和架构
```bash
# 查看当前版本信息
cat version.json

# 记录关键信息:
# - version: 版本号 (如 v2.4.8)
# - test_coverage: 测试覆盖率 (如 95/97)
# - features: 新功能列表
# - codename: 版本代号
```

### 2️⃣ 运行完整测试并更新结果
```bash
# 运行出厂测试
python tests/factory_test.py

# 记录测试结果，更新到 version.json 和相关文档
# 例如: 95/97 通过 (97.9%)
```

### 3️⃣ 检查和更新 .gitignore 对齐
```bash
# 检查 .gitignore 版本标记
head -3 .gitignore

# 确保版本号与代码一致，如需要则更新:
sed -i '' 's/# 版本: v[0-9]\.[0-9]\.[0-9]/# 版本: vNEW_VERSION/g' .gitignore

# 验证临时目录和运行时数据被正确忽略
git status --ignored
```

### 4️⃣ 批量更新所有文档版本号
```bash
# 获取新版本号
NEW_VERSION=$(cat version.json | grep '"version"' | cut -d'"' -f4)
OLD_VERSION="2.4.6"  # 替换为实际的旧版本号

# 批量替换版本号
for file in *.md; do
  sed -i '' "s/v${OLD_VERSION}/v${NEW_VERSION}/g" "$file"
  sed -i '' "s/版本.*v${OLD_VERSION}/版本**: v${NEW_VERSION}/g" "$file"
  sed -i '' "s/Version.*v${OLD_VERSION}/版本**: v${NEW_VERSION}/g" "$file"
done

echo "版本号更新完成: v${NEW_VERSION}"
```

### 5️⃣ 同步测试覆盖率到所有相关文档
```bash
# 从 version.json 提取测试数据
COVERAGE=$(cat version.json | grep '"test_coverage"' | cut -d'"' -f4)
PASSED=$(echo $COVERAGE | cut -d'/' -f1)
TOTAL=$(echo $COVERAGE | cut -d'/' -f2)
PERCENT=$(echo "scale=1; $PASSED * 100 / $TOTAL" | bc)

# 更新 README.md 徽章
sed -i '' "s/test%20coverage-[0-9.]*%25/test%20coverage-${PERCENT}%25/g" README.md

# 更新 TESTING.md 结果
sed -i '' "s/[0-9]*\/97/${COVERAGE}/g" TESTING.md
sed -i '' "s/[0-9.]*%/${PERCENT}%/g" TESTING.md

echo "测试覆盖率更新: ${PERCENT}% (${COVERAGE})"
```

### 6️⃣ 更新 CHANGELOG.md 新版本记录
```bash
# 手动编辑 CHANGELOG.md，在开头添加新版本记录
# 模板:
```
```markdown
## v${NEW_VERSION} ($(date +%Y-%m-%d)) - [版本代号]

### 🚀 新功能
- [从 version.json features 获取]

### 🐛 修复  
- [具体修复内容]

### 🔧 优化
- [性能和体验优化]

### 📊 测试
- 测试覆盖率: ${PERCENT}% (${COVERAGE})

---
```

### 7️⃣ 检查缺少版本标记的文档
```bash
# 检查所有文档版本对齐情况
echo "=== 版本对齐检查 ==="
for file in *.md; do
  if ! grep -q "v${NEW_VERSION}" "$file"; then
    echo "❌ 需要手动更新: $file"
  else
    echo "✅ 已对齐: $file"
  fi
done
```

### 8️⃣ 手动添加版本标记到规范文档
```bash
# 对于开发规范类文档，添加版本标记
CURRENT_DATE=$(date +%Y-%m-%d)

for file in CONTRIBUTING.md DEVELOPMENT_CLEANUP_STANDARD.md DEVELOPMENT_STANDARD.md NON_ESSENTIAL_PUSH_STANDARD.md; do
  if [ -f "$file" ] && ! grep -q "版本.*v${NEW_VERSION}" "$file"; then
    sed -i '' "2i\\
**版本**: v${NEW_VERSION}  \\
**更新日期**: ${CURRENT_DATE}\\
" "$file"
    echo "✅ 已添加版本标记: $file"
  fi
done
```

### 9️⃣ 验证所有环节对齐完成
```bash
# 检查文档版本对齐
DOC_COUNT=$(grep -l "v${NEW_VERSION}" *.md | wc -l | tr -d ' ')
TOTAL_DOCS=$(ls *.md | wc -l | tr -d ' ')
echo "📄 文档对齐: ${DOC_COUNT}/${TOTAL_DOCS}"

# 检查 .gitignore 版本
GITIGNORE_VERSION=$(head -3 .gitignore | grep "版本" | grep -o "v[0-9]\.[0-9]\.[0-9]")
echo "📋 .gitignore 版本: ${GITIGNORE_VERSION}"

# 检查测试覆盖率同步
README_COVERAGE=$(grep -o "test%20coverage-[0-9.]*%" README.md)
echo "📊 README 测试覆盖率: ${README_COVERAGE}"

# 检查是否有未跟踪的重要文件
echo "📁 Git 状态检查:"
git status --porcelain
```

### 🔟 清理临时文件和运行时数据
```bash
# 清理临时文件 (按 .gitignore 规则)
rm -f crawler_state_*.json
rm -rf temp_uploads/*
rm -rf exports/*
find . -name "*.tmp" -delete
find . -name "*.temp" -delete

# 清理测试产生的临时文件
rm -f test_*.json
rm -f *_test_output.txt

echo "🧹 临时文件清理完成"
```

### 1️⃣1️⃣ 提交所有更新
```bash
# 添加所有更改
git add .

# 生成标准化提交信息
FEATURES=$(cat version.json | grep -A 10 '"features"' | grep -o '"[^"]*"' | sed 's/"//g' | head -3 | paste -sd ',' -)

git commit -m "docs: 完整准备工作 - 对齐所有环节到 v${NEW_VERSION}

✅ 文档对齐:
- ${DOC_COUNT}个文档全部更新版本标记到 v${NEW_VERSION}
- 同步测试覆盖率到 ${PERCENT}% (${COVERAGE})
- 完善 CHANGELOG 记录版本特性

✅ 测试更新:
- 运行完整出厂测试 (${COVERAGE})
- 同步测试结果到相关文档

✅ 环境对齐:
- .gitignore 版本更新到 v${NEW_VERSION}
- 清理临时文件和运行时数据

🎯 核心特性:
${FEATURES}"
```

### 1️⃣2️⃣ 推送到 GitHub
```bash
# 推送到远程仓库
git push origin main

# 确认推送成功
echo "🚀 推送状态检查:"
git status
git log --oneline -2
```

### 1️⃣3️⃣ 最终验证
```bash
# 获取远程最新信息
git fetch origin

# 确认本地与远程同步
if [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ]; then
  echo "✅ 本地与远程完全同步"
else
  echo "❌ 同步异常，请检查"
fi

# 显示最终状态
echo "🎉 完整准备工作完成!"
echo "📋 版本: v${NEW_VERSION}"
echo "📊 测试覆盖率: ${PERCENT}%"
echo "📄 文档对齐: ${DOC_COUNT}/${TOTAL_DOCS}"
echo "🔗 GitHub: https://github.com/zhaosj0315/rag-pro-max"
```

---

## 📋 完整检查清单

### 🔥 核心文档 (必须对齐)
- [ ] **version.json** - 版本基准数据
- [ ] **README.md** - 版本徽章 + 测试覆盖率徽章
- [ ] **CHANGELOG.md** - 新版本详细更新记录
- [ ] **USER_MANUAL.md** - 用户手册版本标记
- [ ] **TESTING.md** - 最新测试结果和覆盖率
- [ ] **API.md** - API文档版本标记
- [ ] **ARCHITECTURE.md** - 架构文档版本标记
- [ ] **DEPLOYMENT.md** - 部署指南版本标记
- [ ] **FAQ.md** - 常见问题版本标记
- [ ] **FIRST_TIME_GUIDE.md** - 首次使用指南版本

### 📄 辅助文档 (按需对齐)
- [ ] **ANDROID_COMPATIBILITY_ANALYSIS.md** - Android兼容性分析
- [ ] **CONTRIBUTING.md** - 贡献指南
- [ ] **DEVELOPMENT_CLEANUP_STANDARD.md** - 开发清理标准
- [ ] **DEVELOPMENT_STANDARD.md** - 开发规范标准
- [ ] **DOCUMENTATION_MAINTENANCE_STANDARD.md** - 文档维护标准
- [ ] **NON_ESSENTIAL_PUSH_STANDARD.md** - 推送规范标准

### 🧪 测试环节 (必须更新)
- [ ] **运行出厂测试** - `python tests/factory_test.py`
- [ ] **更新测试覆盖率** - 同步到 version.json
- [ ] **更新 README 徽章** - 测试覆盖率百分比
- [ ] **更新 TESTING.md** - 最新测试结果记录

### 📁 环境对齐 (必须检查)
- [ ] **.gitignore 版本** - 确保版本标记一致
- [ ] **临时文件清理** - 删除所有临时和测试文件
- [ ] **运行时数据清理** - 清空 temp_uploads, exports 等
- [ ] **Git 状态检查** - 确保没有遗漏重要文件

### 🚀 推送准备 (必须完成)
- [ ] **提交信息标准化** - 包含版本、特性、测试结果
- [ ] **推送到 GitHub** - 确保远程同步
- [ ] **最终验证** - 本地与远程一致性检查

---

## ⚡ 一键执行脚本

```bash
#!/bin/bash
# 代码开发完成后一键执行脚本

set -e  # 遇到错误立即退出

echo "🚀 开始执行完整准备工作..."

# 1. 获取版本信息
NEW_VERSION=$(cat version.json | grep '"version"' | cut -d'"' -f4)
echo "📋 当前版本: v${NEW_VERSION}"

# 2. 运行测试
echo "🧪 运行出厂测试..."
python tests/factory_test.py

# 3. 更新文档版本
echo "📄 更新文档版本..."
OLD_VERSION="2.4.6"  # 需要手动更新
for file in *.md; do
  sed -i '' "s/v${OLD_VERSION}/v${NEW_VERSION}/g" "$file"
done

# 4. 同步测试覆盖率
echo "📊 同步测试覆盖率..."
COVERAGE=$(cat version.json | grep '"test_coverage"' | cut -d'"' -f4)
PASSED=$(echo $COVERAGE | cut -d'/' -f1)
TOTAL=$(echo $COVERAGE | cut -d'/' -f2)
PERCENT=$(echo "scale=1; $PASSED * 100 / $TOTAL" | bc)
sed -i '' "s/test%20coverage-[0-9.]*%25/test%20coverage-${PERCENT}%25/g" README.md

# 5. 更新 .gitignore 版本
echo "📋 更新 .gitignore..."
sed -i '' "s/# 版本: v[0-9]\.[0-9]\.[0-9]/# 版本: v${NEW_VERSION}/g" .gitignore

# 6. 清理临时文件
echo "🧹 清理临时文件..."
rm -f crawler_state_*.json
rm -rf temp_uploads/* 2>/dev/null || true
rm -rf exports/* 2>/dev/null || true

# 7. 验证对齐
echo "✅ 验证对齐完成..."
DOC_COUNT=$(grep -l "v${NEW_VERSION}" *.md | wc -l | tr -d ' ')
TOTAL_DOCS=$(ls *.md | wc -l | tr -d ' ')
echo "📄 文档对齐: ${DOC_COUNT}/${TOTAL_DOCS}"

# 8. 提交推送
echo "🚀 提交并推送..."
git add .
git commit -m "docs: 完整准备工作 - 对齐所有环节到 v${NEW_VERSION}"
git push origin main

echo "🎉 完整准备工作完成!"
echo "📋 版本: v${NEW_VERSION}"
echo "📊 测试覆盖率: ${PERCENT}%"
echo "📄 文档对齐: ${DOC_COUNT}/${TOTAL_DOCS}"
```

---

## ⚠️ 重要注意事项

1. **执行顺序**: 严格按照步骤顺序执行，确保依赖关系正确
2. **版本号检查**: 执行前确认 version.json 中的版本号已更新
3. **测试先行**: 必须先运行测试，确保代码质量后再更新文档
4. **备份保护**: 建议执行前创建 Git 分支备份
5. **手动检查**: CHANGELOG.md 需要手动编写，描述具体更新内容
6. **环境清理**: 确保临时文件和运行时数据被正确清理
7. **最终验证**: 推送后验证 GitHub 上的内容是否正确

---

**使用说明**: 代码开发完成后，按此清单执行可确保文档、测试、环境等所有环节逻辑统一一致，为推送做好完整的前置准备工作。
