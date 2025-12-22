# 常见问题 (FAQ)

**版本**: v2.4.8**  
**更新日期**: 2025-12-18

## 📋 目录

- [v2.0 新功能](#v20-新功能)
- [安装和配置](#安装和配置)
- [使用问题](#使用问题)
- [性能优化](#性能优化)
- [故障排除](#故障排除)
- [高级功能](#高级功能)
- [维护和开发](#维护和开发)

---

## v2.0 新功能

### Q: 如何使用增量更新功能？

**A**: 
1. 确保安装了v2.0依赖: `./scripts/deploy_v2.sh`
2. 在Web界面的侧边栏找到"📈 增量更新"部分
3. 上传文件后点击"🔍 检查文件变化"
4. 系统会显示新增、修改、未变化的文件
5. 点击"🚀 执行增量更新"只处理变化的文件

### Q: 多模态功能支持哪些格式？

**A**: 
- **图片**: JPG, JPEG, PNG, BMP, TIFF, GIF (需要Tesseract OCR)
- **表格**: PDF表格, Excel (.xlsx/.xls), CSV (需要Java环境)
- **文档**: 所有原有格式 + 图片和表格内容提取

### Q: 如何安装OCR和表格提取依赖？

**A**:
```bash
# macOS
brew install tesseract tesseract-lang
brew install openjdk

# Ubuntu/Debian  
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-eng
sudo apt-get install openjdk-8-jdk

# 然后安装Python依赖
pip install -r requirements_v2.txt
```

### Q: v2.0和v1.8有什么区别？

**A**: v2.0完全向后兼容v1.8，新增功能：
- ✅ 增量更新 - 只处理变化文件，效率提升70-90%
- ✅ 多模态支持 - 图片OCR + 表格提取
- ✅ API扩展 - 新增4个RESTful接口
- ✅ 智能启动 - 自动检测功能可用性

## 安装和配置

### Q: 支持哪些 Python 版本？

**A**: Python 3.8 及以上版本。推荐使用 Python 3.10 或 3.12。

```bash
python --version  # 检查版本
```

### Q: 如何安装依赖？

**A**: 使用 pip 安装：

```bash
pip install -r requirements.txt
```

如果遇到网络问题，可以使用国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: 首次启动需要下载什么？

**A**: 首次启动会自动下载：

- **嵌入模型**: BAAI/bge-small-zh-v1.5 (~400MB)
- **Re-ranking 模型**: BAAI/bge-reranker-base (~1GB，如果启用）

下载位置：`./hf_cache/`

### Q: 如何配置 Ollama？

**A**: 

1. 安装 Ollama:
```bash
brew install ollama  # macOS
```

2. 启动服务:
```bash
ollama serve
```

3. 下载模型:
```bash
ollama pull qwen2.5:7b
```

4. 在应用中配置:
- API Base URL: `http://localhost:11434`
- 模型: `qwen2.5:7b`

### Q: 如何配置 OpenAI？

**A**:

1. 获取 API Key: https://platform.openai.com/api-keys

2. 在应用中配置:
- API Base URL: `https://api.openai.com/v1`
- API Key: `sk-your-key-here`
- 模型: `gpt-3.5-turbo` 或 `gpt-4`

或设置环境变量:
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

---

## 使用问题

### Q: 上传文档后没有反应？

**A**: 检查以下几点：

1. **文档格式**: 确保是支持的格式（PDF、DOCX、TXT、MD 等）
2. **文件大小**: 单个文件不超过 100MB
3. **控制台日志**: 查看是否有错误信息
4. **LLM 配置**: 确保 LLM 已正确配置

### Q: 知识库显示"暂无文档"但统计数据显示有文件？

**A**: 
- **原因**: 知识库对应的原始文件可能已被删除或移动，但元数据仍存在。
- **解决**: 在 v2.4.8+ 版本中，系统会自动基于元数据显示文件记录，允许您查看和管理，即使物理文件缺失。建议重新上传文件或删除该失效记录。

### Q: 对话没有引用来源？

**A**: 可能的原因：

1. **知识库为空**: 确保已上传文档
2. **相似度阈值**: 调整 `rag_config.json` 中的 `similarity_threshold`
3. **查询不相关**: 问题与知识库内容不匹配

### Q: 如何提高答案准确率？

**A**: 多种方法：

1. **开启 Re-ranking**: 准确率 +10-20%
2. **开启 BM25 混合检索**: 准确率 +5-10%
3. **优化文档质量**: 上传高质量、结构化的文档
4. **调整参数**: 修改 `chunk_size` 和 `top_k`

### Q: 支持哪些文档格式？

**A**: 支持以下格式：

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| PDF | .pdf | 支持文本提取 |
| Word | .docx | 支持表格和图片 |
| 文本 | .txt | 纯文本 |
| Markdown | .md | 支持格式化 |
| Excel | .xlsx | 支持多个工作表 |
| PowerPoint | .pptx | 支持幻灯片 |
| CSV | .csv | 表格数据 |
| HTML | .html | 网页内容 |
| JSON | .json | 结构化数据 |
| 压缩包 | .zip | 批量上传 |

### Q: 如何批量上传文档？

**A**: 两种方式：

1. **文件夹上传**: 点击"批量上传文件夹"，选择包含文档的文件夹
2. **ZIP 上传**: 将文档打包成 ZIP，直接上传

### Q: 对话历史保存在哪里？

**A**: 保存在 `chat_histories/` 目录：

```
chat_histories/
  └── 知识库名称.json
```

可以手动备份或删除。

---

## 性能优化

### Q: 为什么 CPU 只用了 30-40%？

**A**: GPU 是瓶颈。

向量化任务主要靠 GPU 计算，CPU 只是准备数据。GPU 已经 99% 满载，CPU 再多也无法提升性能。

### Q: 如何加快文档处理速度？

**A**: 几个方法：

1. **减少文档数量**: 只上传必要的文档
2. **优化文档格式**: 使用 TXT 或 MD 格式（处理更快）
3. **调整 chunk_size**: 增大 chunk_size 减少分块数量
4. **使用 GPU**: 确保 GPU 可用

### Q: 查询速度慢怎么办？

**A**: 优化建议：

1. **关闭 Re-ranking**: 如果不需要极高准确率
2. **关闭 BM25**: 减少检索时间
3. **减少 top_k**: 检索更少的文档
4. **使用更快的 LLM**: 如 gpt-3.5-turbo

### Q: 内存占用太高？

**A**: 减少内存占用：

1. **关闭 Re-ranking**: 节省 ~1GB
2. **减少知识库数量**: 只加载需要的
3. **清理缓存**: 删除 `hf_cache/` 中不用的模型
4. **重启应用**: 释放内存

---

## 故障排除

### Q: 启动时报错 "ModuleNotFoundError"？

**A**: 缺少依赖包：

```bash
pip install -r requirements.txt
```

### Q: 嵌入模型加载失败？

**A**: 可能的原因：

1. **网络问题**: 无法连接 HuggingFace
   - 解决：使用镜像或手动下载模型

2. **磁盘空间不足**: 模型需要 ~400MB
   - 解决：清理磁盘空间

3. **权限问题**: 无法写入 `hf_cache/`
   - 解决：检查目录权限

### Q: Ollama 连接失败？

**A**: 检查步骤：

1. **服务是否启动**:
```bash
curl http://localhost:11434/api/tags
```

2. **端口是否正确**: 默认 11434

3. **模型是否下载**:
```bash
ollama list
```

### Q: GPU 不可用？

**A**: 检查 GPU 状态：

```bash
# macOS
sudo python3 src/system_monitor.py

# 查看 GPU 信息
```

如果 GPU 不可用，系统会自动使用 CPU（速度较慢）。

### Q: 出厂测试失败？

**A**: 查看失败的测试项：

```bash
./scripts/test.sh
```

根据错误信息修复问题，常见原因：
- 依赖包未安装
- 配置文件格式错误
- 模型缓存损坏

### Q: 点击预览按钮后没有反应，或提示“无法定位文件”？

**A**: 可能的原因及解决方法：

1. **Manifest 记录过旧**: 如果知识库是 v2.4.8 之前构建的，清单中可能未记录绝对路径。
   - **解决**: 点击侧边栏的 `🔄`（重建索引）按钮刷新清单。
2. **预览窗口在后台**: 虽然系统尝试自动置顶，但在某些 macOS 权限限制下可能失败。
   - **解决**: 使用 `Command + Tab` 切换或检查是否有弹出的 `qlmanage` 窗口。
3. **系统权限**: macOS 可能会拦截通过 AppleScript 控制的窗口置顶。
   - **解决**: 确保终端/Python 拥有控制“系统事件”的权限（设置 -> 隐私与安全性 -> 自动化）。

### Q: 为什么点击上传文件后，按钮会再次弹出？

**A**: 这是 v2.4.8 之前的一个交互 Bug。
- **解决**: 请升级到 v2.4.8。新版本引入了 `upload_hash` 校验机制，只有当文件内容真正改变时才会触发处理，彻底解决了“上传两次”的问题。

---

## 高级功能

### Q: Re-ranking 和 BM25 可以同时开启吗？

**A**: 可以！效果叠加：

```
查询 → BM25 混合检索 (Top 10) → Re-ranking (Top 3)
```

**准确率提升**: 15-30%  
**延迟增加**: 1-2 秒

### Q: 如何自定义嵌入模型？

**A**: 修改配置：

1. 在侧边栏选择 "HuggingFace (本地/极速)"
2. 输入模型名称，如 `BAAI/bge-m3`
3. 点击"📥 下载模型"

支持所有 HuggingFace 上的 sentence-transformers 模型。

### Q: 如何导出对话记录？

**A**: 

1. 在侧边栏找到"🛠️ 聊天控制"
2. 点击"📥 导出对话"
3. 点击"💾 下载 Markdown"

导出格式为 Markdown，可用任何文本编辑器打开。

### Q: 如何查看系统资源使用情况？

**A**: 两种方式：

1. **侧边栏监控**: 点击"📊 系统监控"（简化版）
2. **命令行监控**: `sudo python3 src/system_monitor.py`（详细版）

### Q: 支持多用户吗？

**A**: 当前版本不支持。

**临时方案**: 
- 每个用户打开独立的浏览器窗口
- 使用不同的知识库

**未来计划**: v2.6 将支持多用户系统

### Q: 可以通过 API 调用吗？

**A**: **支持 (v2.0+)**。

如果您的系统安装了 v2.0 模块（IncrementalUpdater等），启动时会自动开启 FastAPI 服务（端口 8000）。

- **API文档**: `http://localhost:8000/docs`
- **基础URL**: `http://localhost:8000/api`

### Q: 如何备份知识库？

**A**: 备份以下目录：

```bash
# 备份向量数据库
cp -r vector_db_storage/ backup/

# 备份对话历史
cp -r chat_histories/ backup/

# 备份配置
cp app_config.json backup/
```

恢复时复制回原位置即可。

---

## 其他问题

### Q: 如何贡献代码？

**A**: 查看 [CONTRIBUTING.md](CONTRIBUTING.md)

### Q: 如何报告 Bug？

**A**: 在 GitHub 创建 Issue，提供：
- 详细的复现步骤
- 错误信息和日志
- 系统环境信息

### Q: 有使用教程吗？

**A**: 查看以下文档：
- [README.md](README.md) - 快速开始
- [FIRST_TIME_GUIDE.md](FIRST_TIME_GUIDE.md) - 新手引导
- [TESTING.md](TESTING.md) - 测试说明

### Q: 支持哪些操作系统？

**A**: 
- ✅ macOS (推荐)
- ✅ Linux
- ✅ Docker (跨平台)
- ✅ Windows (支持但需配置)

### Q: 商业使用需要授权吗？

**A**: 不需要。

本项目采用 MIT 许可证，可以自由用于商业用途。

---

## 仍有问题？

- **GitHub Issues**: https://github.com/yourusername/rag-pro-max/issues
- **Discussions**: https://github.com/yourusername/rag-pro-max/discussions
- **Email**: your-email@example.com

---

**最后更新**: 2025-12-17


---

## 维护和开发

### Q: 如何检查文档是否与代码同步？
**A**: 运行文档同步检查脚本：
```bash
python scripts/check_documentation_sync.py
```
该脚本会检查版本号一致性、API文档完整性、配置文档同步等。

### Q: 推送代码前需要做什么检查？
**A**: 运行推送前安全检查：
```bash
./scripts/pre_push_safety_check.sh
```
确保遵守"非必要不推送"原则，防止私有数据推送到远程。

### Q: 哪些文件不应该推送到远程仓库？
**A**: 以下文件类型不应推送：
- 用户数据: `vector_db_storage/`, `chat_histories/`
- 缓存文件: `hf_cache/`, `__pycache__/`
- 日志文件: `app_logs/`, `*.log`
- 临时文件: `temp_uploads/`, `exports/`, `crawler_state*.json`
- 系统文件: `.DS_Store`, `*.pyc`

### Q: 代码更新后需要维护哪些文档？
**A**: 参考 `DOCUMENTATION_MAINTENANCE_STANDARD.md`：
- **必须更新**: `version.json`, `CHANGELOG.md`, `README.md`
- **功能变更时**: `USER_MANUAL.md`, `API.md`, `ARCHITECTURE.md`
- **配置变更时**: `DEPLOYMENT.md`, `FAQ.md`

### Q: 如何运行出厂测试？
**A**: 
```bash
# 完整测试
python tests/factory_test.py

# 快速测试
python tests/factory_test.py --quick
```
确保测试通过率 ≥ 85% 才能发布。
