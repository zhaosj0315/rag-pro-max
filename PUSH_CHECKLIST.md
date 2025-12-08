# Git 推送清单

## 原则：非必要不推送

只推送运行项目所需的最小文件集，排除所有运行时数据、用户配置、缓存和内部文档。

---

## ✅ 应该推送的文件

### 1. 源代码
- `src/*.py` - 所有 Python 源文件
- `src/utils/*.py` - 工具模块

### 2. 测试代码
- `tests/*.py` - 所有测试文件

### 3. 脚本
- `scripts/*.sh` - 启动、构建、测试脚本

### 4. 配置模板（仅模板）
- `config/app_config.json` - 应用配置模板
- `config/rag_config.json` - RAG 配置模板
- `config/projects_config.json` - 项目配置模板

### 5. 部署文件
- `Dockerfile` - Docker 镜像配置
- `docker-compose.yml` - Docker 编排
- `RAG_Pro_Max.spec` - PyInstaller 打包配置

### 6. 文档（仅用户文档）
- `README.md` - 项目说明
- `LICENSE` - 许可证

### 7. 其他必要文件
- `.gitignore` - Git 忽略规则
- `requirements.txt` - Python 依赖
- `kbllama` - 命令行工具

---

## ❌ 不应该推送的文件

### 1. 运行时数据
- `vector_db_storage/` - 向量数据库
- `chat_histories/` - 对话历史
- `temp_uploads/` - 临时上传文件
- `app_logs/` - 应用日志

### 2. 用户配置（根目录）
- `app_config.json` - 用户应用配置
- `rag_config.json` - 用户 RAG 配置
- `projects_config.json` - 用户项目配置

### 3. 缓存文件
- `hf_cache/` - HuggingFace 模型缓存
- `__pycache__/` - Python 字节码缓存
- `*.pyc`, `*.pyo`, `*.pyd` - 编译文件

### 4. 构建产物
- `dist/` - 打包输出
- `build/` - 构建临时文件

### 5. 内部开发文档
- `CHANGELOG.md` - 变更日志
- `TESTING.md` - 测试文档
- `FAQ.md` - 常见问题
- `DEPLOYMENT.md` - 部署指南
- `CONTRIBUTING.md` - 贡献指南
- `DOCS_INDEX.md` - 文档索引
- `RERANK.md` - 重排序文档
- `BM25.md` - BM25 文档
- `UX_IMPROVEMENTS.md` - UX 改进文档
- `FIRST_TIME_GUIDE.md` - 首次使用指南
- `docs/` - 文档目录

### 6. 系统文件
- `.DS_Store` - macOS 系统文件

---

## 🔍 推送前检查

### 方法 1：使用检查脚本（推荐）
```bash
./scripts/check_push.sh
```

### 方法 2：手动检查
```bash
# 查看待推送文件
git ls-files

# 检查文件数量（应该在 40 个左右）
git ls-files | wc -l

# 检查是否有不该推送的文件
git ls-files | grep -E "(vector_db_storage|chat_histories|temp_uploads|hf_cache|app_logs|__pycache__|dist|build)"
```

---

## 📝 推送流程

1. **修改代码后**
   ```bash
   git add src/ tests/ scripts/ config/
   git add README.md LICENSE requirements.txt
   git add Dockerfile docker-compose.yml RAG_Pro_Max.spec
   ```

2. **运行检查**
   ```bash
   ./scripts/check_push.sh
   ```

3. **提交并推送**
   ```bash
   git commit -m "描述你的修改"
   git push
   ```

---

## 🚨 如果不小心推送了不该推送的文件

```bash
# 从 Git 中删除（但保留本地文件）
git rm --cached <文件名>

# 提交删除
git commit -m "chore: 移除不该推送的文件"

# 推送
git push
```

---

## 📊 当前推送文件统计

- 总文件数: 39 个
- 源代码: 11 个
- 工具模块: 9 个
- 测试: 6 个
- 脚本: 4 个
- 配置模板: 3 个
- 部署文件: 3 个
- 文档: 2 个
- 其他: 1 个

**总大小**: 约 576KB
