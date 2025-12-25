# 代码维护完成后文档更新标准

## 📋 必须维护到最新版本的文档清单

### 🔥 每次代码更新必须同步的文档

#### 1. 版本信息文档
- [ ] **version.json** - 版本号必须更新
- [ ] **CHANGELOG.md** - 新增版本更新记录
- [ ] **README.md** - 版本徽章和新功能说明

#### 2. 功能变更文档  
- [ ] **README.md** - 核心功能列表同步
- [ ] **USER_MANUAL.md** - 新功能使用说明
- [ ] **API.md** - 新增/修改的API接口

#### 3. 技术架构文档
- [ ] **ARCHITECTURE.md** - 架构变更说明
- [ ] **requirements.txt** - 依赖包版本更新
- [ ] **DEPLOYMENT.md** - 部署步骤变更

#### 4. 配置相关文档
- [ ] **config/** 目录说明 - 新增配置项说明
- [ ] **FAQ.md** - 新问题和解决方案
- [ ] **TESTING.md** - 测试用例更新

---

## 🔍 文档同步检查流程

### Step 1: 版本信息同步
```bash
# 检查版本一致性
grep -r "v2\.4\.4" README.md CHANGELOG.md version.json
```

### Step 2: 功能描述同步
```bash
# 检查功能列表是否与代码一致
grep -r "核心功能\|主要特性" README.md USER_MANUAL.md
```

### Step 3: API文档同步
```bash
# 检查API接口是否完整
find src/ -name "*.py" -exec grep -l "def.*api\|@app\." {} \;
```

### Step 4: 配置文档同步
```bash
# 检查配置文件说明
ls config/ && grep -r "config" DEPLOYMENT.md README.md
```

---

## ⚡ 快速维护命令

### 批量更新版本号
```bash
# 更新所有文档中的版本号
sed -i '' 's/v2\.5\.1/v2.6.0/g' README.md CHANGELOG.md
```

### 检查文档完整性
```bash
# 运行文档完整性检查
python tests/check_documentation_sync.py
```

### 生成更新报告
```bash
# 生成文档更新报告
./scripts/generate_doc_update_report.sh
```

---

## 📝 维护责任清单

| 文档类型 | 维护频率 | 负责人 | 检查点 |
|---------|---------|--------|--------|
| README.md | 每次发布 | 主开发者 | 功能列表、版本号 |
| CHANGELOG.md | 每次提交 | 提交者 | 变更记录 |
| API.md | API变更时 | 后端开发者 | 接口文档 |
| USER_MANUAL.md | UI变更时 | 前端开发者 | 界面说明 |
| DEPLOYMENT.md | 部署变更时 | 运维负责人 | 部署步骤 |

---

## ✅ 维护完成检查

- [ ] 所有版本号已更新一致
- [ ] 新功能已添加到README.md
- [ ] CHANGELOG.md已记录本次变更
- [ ] 相关配置文档已同步
- [ ] API文档已更新
- [ ] 部署文档已验证可用

**维护完成标志**: 所有复选框都已勾选 ✅
