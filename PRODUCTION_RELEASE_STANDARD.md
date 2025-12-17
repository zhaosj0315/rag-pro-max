# RAG Pro Max 出厂标准流程

## 🎯 出厂原则

**核心原则**: 非必要不推送 - 只推送项目启动和运行的核心材料

## 📋 出厂前强制清单

### 🔥 第一阶段：用户数据清理 (必须执行)

#### 1. 删除用户测试数据
```bash
# 清空测试知识库
rm -rf vector_db_storage/*
echo "" > vector_db_storage/.gitkeep

# 清空聊天历史
rm -rf chat_histories/*
echo "" > chat_histories/.gitkeep

# 清空临时上传
rm -rf temp_uploads/*

# 清空应用日志
rm -rf app_logs/*
echo "" > app_logs/.gitkeep

# 删除爬虫状态文件
rm -f crawler_state_*.json
rm -f detected_cycles.csv

# 删除系统文件
find . -name ".DS_Store" -delete
find . -name "Thumbs.db" -delete

# ⚠️ 保留本地缓存 - 仅通过 .gitignore 不推送
# hf_cache/ - 保留本地模型缓存，加速后续使用
# 其他本地优化缓存也保留
```

#### 2. 重置配置文件
```bash
# 重置应用配置为出厂默认值
cat > config/app_config.json << EOF
{
  "version": "2.4.4",
  "first_run": true,
  "default_model": "qwen2.5:7b",
  "max_file_size": 104857600
}
EOF

# 清空历史记录
echo "[]" > config/alert_history.json
echo "[]" > config/scheduler_history.json
echo "{}" > config/monitoring_history.json
echo "{}" > config/performance_history.json
```

#### 3. 清理缓存和临时文件
```bash
# 清理Python缓存
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete

# 清理测试结果
rm -f test_results.json

# 清理开发文件
rm -f src/apppro.py.pre-migration
rm -f *_backup.py
rm -f *_old.py
```

### 🔥 第二阶段：版本信息同步 (必须执行)

#### 4. 统一版本号
- [ ] 检查 `version.json` 版本号
- [ ] 同步 `src/core/version.py` 版本
- [ ] 更新 `README.md` 版本徽章
- [ ] 更新 `CHANGELOG.md` 最新版本
- [ ] 同步 `docker-compose.yml` 镜像版本

#### 5. 文档版本对齐
```bash
# 自动更新所有文档中的版本引用
sed -i '' 's/v[0-9]\+\.[0-9]\+\.[0-9]\+/v2.4.4/g' *.md
sed -i '' 's/version-v[0-9]\+\.[0-9]\+\.[0-9]\+-/version-v2.4.4-/g' README.md
```

### 🔥 第三阶段：文档维护 (必须执行)

#### 6. 核心文档更新检查
- [ ] `README.md` - 功能描述与代码一致
- [ ] `API.md` - 接口文档与实际API一致  
- [ ] `ARCHITECTURE.md` - 架构图与代码结构一致
- [ ] `DEPLOYMENT.md` - 部署步骤可执行
- [ ] `requirements.txt` - 依赖版本锁定

#### 7. 删除开发阶段文档
```bash
# 删除重构和开发过程文档
rm -f REFACTOR_PROGRESS_RECORD.md
rm -f PHASE_*.md
rm -f GRADUAL_REFACTOR_PLAN.md
rm -f PROJECT_STRUCTURE_V*.md  # 保留最新版本
```

### 🔥 第四阶段：代码质量检查 (必须执行)

#### 8. 代码清理
- [ ] 移除所有 `print()` 调试语句
- [ ] 删除 `# TODO` 和 `# FIXME` 注释
- [ ] 清理未使用的导入
- [ ] 移除硬编码的测试数据

#### 9. 安全检查
- [ ] 确认无API密钥硬编码
- [ ] 检查无敏感路径泄露
- [ ] 验证默认配置安全性
- [ ] 确认示例数据无隐私信息

### 🔥 第五阶段：功能验证 (必须执行)

#### 10. 出厂测试
```bash
# 运行出厂测试套件
python tests/factory_test.py

# 验证核心功能
python -c "
import sys
sys.path.append('src')
from services.file_service import FileService
from services.knowledge_base_service import KnowledgeBaseService
print('✅ 核心服务导入成功')
"

# 验证启动
streamlit run src/apppro.py --server.headless true --server.port 8502 &
sleep 10
curl -f http://localhost:8502 && echo '✅ 应用启动成功' || echo '❌ 启动失败'
pkill -f streamlit
```

## 📦 允许推送的文件清单

### ✅ 核心代码文件
```
src/                    # 所有源代码
├── apppro.py          # 主应用
├── services/          # 服务层
├── common/            # 公共层
├── ui/                # 界面层
├── processors/        # 处理器
├── utils/             # 工具层
├── core/              # 核心层
├── kb/                # 知识库
├── chat/              # 聊天功能
├── api/               # API接口
├── config/            # 配置模块
├── engines/           # 引擎
├── query/             # 查询
├── monitoring/        # 监控
├── app/               # 应用
├── app_logging/       # 日志
├── documents/         # 文档管理
├── upload/            # 上传
├── queue/             # 队列
├── summary/           # 摘要
└── monitor/           # 系统监控
```

### ✅ 配置文件
```
config/
├── rag_config.json           # RAG配置模板
├── projects_config.json      # 项目配置
├── users.json               # 用户配置模板
├── cpu_protection.json      # CPU保护配置
├── aggressive_processing.json # 处理配置
├── intelligent_processing.json # 智能处理
├── enhancements.json        # 增强配置
└── alert_config.json        # 告警配置
```

### ✅ 核心文档
```
README.md              # 项目说明
API.md                 # API文档
ARCHITECTURE.md        # 架构文档
DEPLOYMENT.md          # 部署指南
CHANGELOG.md           # 更新日志
LICENSE               # 许可证
CONTRIBUTING.md       # 贡献指南
FAQ.md                # 常见问题
TESTING.md            # 测试说明
USER_MANUAL.md        # 用户手册
FIRST_TIME_GUIDE.md   # 首次使用指南
```

### ✅ 部署文件
```
requirements.txt       # Python依赖
Dockerfile            # Docker构建
docker-compose.yml    # Docker编排
.streamlit/           # Streamlit配置
scripts/              # 部署脚本
├── deploy_linux.sh
├── deploy_windows.bat
├── docker-build.sh
└── start.sh
```

### ✅ 测试文件
```
tests/                # 测试套件
├── factory_test.py   # 出厂测试
└── test_*.py         # 功能测试
```

### ✅ 工具文件
```
tools/                # 开发工具
├── code_analyzer.py
├── test_validator.py
└── auto_backup.py
```

## 🚫 禁止推送的文件清单

### ❌ 运行时数据
```
vector_db_storage/    # 向量数据库 (保留.gitkeep)
chat_histories/       # 聊天历史 (保留.gitkeep)
temp_uploads/         # 临时上传
app_logs/            # 应用日志 (保留.gitkeep)
hf_cache/            # 模型缓存 (保留.gitkeep)
suggestion_history/   # 建议历史 (保留.gitkeep)
exports/             # 导出文件
```

### ❌ 配置运行时文件
```
config/app_config.json      # 运行时配置
config/alert_history.json   # 告警历史
config/scheduler_history.json # 调度历史
config/monitoring_history.json # 监控历史
config/performance_history.json # 性能历史
app_config.json             # 根目录配置
rag_config.json             # 根目录RAG配置
```

### ❌ 临时和状态文件
```
crawler_state_*.json  # 爬虫状态
detected_cycles.csv   # 检测结果
test_results.json     # 测试结果
*.tmp                 # 临时文件
*.log                 # 日志文件
*.pid                 # 进程文件
*.lock               # 锁文件
```

### ❌ 开发文件
```
REFACTOR_PROGRESS_RECORD.md    # 重构记录
PHASE_*.md                     # 阶段文档
GRADUAL_REFACTOR_PLAN.md       # 重构计划
PROJECT_STRUCTURE_V*.md        # 旧版本结构 (保留最新)
src/apppro.py.pre-migration    # 迁移备份
*_backup.py                    # 备份文件
*_old.py                       # 旧版本文件
```

### ❌ 系统文件
```
.DS_Store            # macOS系统文件
Thumbs.db           # Windows系统文件
__pycache__/        # Python缓存
*.pyc               # Python编译文件
*.pyo               # Python优化文件
.pytest_cache/      # 测试缓存
```

## 🔧 .gitignore 出厂版本

```gitignore
# RAG Pro Max - 出厂版 .gitignore
# 版本: v2.4.4

# ===== 运行时数据 (完全忽略) =====
vector_db_storage/*
!vector_db_storage/.gitkeep
chat_histories/*
!chat_histories/.gitkeep
temp_uploads/
app_logs/*
!app_logs/.gitkeep
hf_cache/*
!hf_cache/.gitkeep
suggestion_history/*
!suggestion_history/.gitkeep
exports/

# ===== 配置运行时文件 =====
config/app_config.json
config/alert_history.json
config/scheduler_history.json
config/monitoring_history.json
config/performance_history.json
app_config.json
rag_config.json

# ===== 临时和状态文件 =====
crawler_state_*.json
detected_cycles.csv
test_results.json
*.tmp
*.temp
*.log
*.pid
*.lock

# ===== Python 相关 =====
__pycache__/
*.py[cod]
*$py.class
*.so
.pytest_cache/
.coverage
htmlcov/

# ===== 系统文件 =====
.DS_Store
Thumbs.db
*.swp
*.swo

# ===== 开发文件 =====
REFACTOR_PROGRESS_RECORD.md
PHASE_*.md
GRADUAL_REFACTOR_PLAN.md
*_backup.py
*_old.py
*.pre-migration

# ===== 环境文件 =====
.env
.env.local
venv/
env/
```

## 🚀 出厂执行脚本

```bash
#!/bin/bash
# 出厂准备脚本

echo "🚀 开始出厂准备..."

# 1. 数据清理
echo "📁 清理测试数据..."
rm -rf vector_db_storage/* chat_histories/* temp_uploads/* app_logs/*
echo "" > vector_db_storage/.gitkeep
echo "" > chat_histories/.gitkeep
echo "" > app_logs/.gitkeep

# 2. 清理临时文件
echo "🧹 清理临时文件..."
find . -name ".DS_Store" -delete
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete
rm -f crawler_state_*.json detected_cycles.csv test_results.json

# 3. 重置配置
echo "⚙️ 重置配置文件..."
cat > config/app_config.json << EOF
{
  "version": "2.4.4",
  "first_run": true,
  "default_model": "qwen2.5:7b"
}
EOF

# 4. 清理开发文档
echo "📚 清理开发文档..."
rm -f REFACTOR_PROGRESS_RECORD.md PHASE_*.md GRADUAL_REFACTOR_PLAN.md
rm -f src/apppro.py.pre-migration

# 5. 运行测试
echo "🧪 运行出厂测试..."
python tests/factory_test.py

# 6. 验证启动
echo "✅ 验证应用启动..."
streamlit run src/apppro.py --server.headless true --server.port 8502 &
sleep 10
curl -f http://localhost:8502 && echo "✅ 启动验证成功" || echo "❌ 启动验证失败"
pkill -f streamlit

echo "🎉 出厂准备完成！"
echo "📋 请检查 PRODUCTION_RELEASE_STANDARD.md 确认所有项目已完成"
```

## 📊 出厂质量标准

### 必达指标
- ✅ 启动时间 ≤ 30秒
- ✅ 内存占用 ≤ 4GB (空闲状态)
- ✅ 测试通过率 ≥ 90%
- ✅ 文档覆盖率 = 100%
- ✅ 安全扫描 = 0 高危漏洞

### 代码质量
- ✅ 无调试代码残留
- ✅ 无硬编码敏感信息
- ✅ 无未使用导入
- ✅ 统一代码风格

### 用户体验
- ✅ 首次启动流畅
- ✅ 错误提示友好
- ✅ 文档易于理解
- ✅ 示例完整可用

---

**遵循此标准，确保每次发布都是生产就绪的高质量版本！** 🚀
