# 贡献指南 (Contributing Guide)

**版本**: v3.2.2  
**更新日期**: 2026-01-03  
**适用范围**: 企业级开发与贡献  
**架构标准**: 四层架构，180个模块，92.8%测试覆盖率

感谢你考虑为 RAG Pro Max 做出贡献！

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发流程](#开发流程)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [测试要求](#测试要求)
- [v3.2.2 开发标准](#v322-开发标准)

## v3.2.2 开发标准

### 界面重构原则
- 所有新界面必须遵循4x1扁平布局设计
- 统一触发机制：所有创建任务由侧边栏统一触发
- 防误触设计：确保配置完成后再执行任务
- 新增模块必须通过测试覆盖率检查（目标93%+）

### 统一架构要求
- 完整系统重构，消除所有重复代码
- 遵循四层架构：表现层、服务层、公共层、工具层
- 代码健壮性：修复所有 IndentationError 和 NameError

## 行为准则

### 我们的承诺

为了营造一个开放和友好的环境，我们承诺：

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

## 如何贡献

### 报告 Bug

在提交 Bug 报告前，请：

1. **检查现有 Issues**: 确保问题尚未被报告
2. **使用最新版本**: 确认问题在最新版本中仍然存在
3. **提供详细信息**: 包括复现步骤、预期行为、实际行为

**Bug 报告模板**:

```markdown
**描述**
简要描述问题

**复现步骤**
1. 执行 '...'
2. 点击 '...'
3. 看到错误

**预期行为**
应该发生什么

**实际行为**
实际发生了什么

**环境**
- OS: [e.g. macOS 14.0]
- Python: [e.g. 3.12]
- 版本: [e.g. 1.1.0]

**截图**
如果适用，添加截图

**日志**
相关的日志输出
```

### 提出新功能

在提交功能请求前，请：

1. **检查路线图**: 查看 README.md 中的路线图
2. **搜索现有 Issues**: 确保功能尚未被提出
3. **说明用例**: 解释为什么需要这个功能

**功能请求模板**:

```markdown
**功能描述**
简要描述新功能

**使用场景**
什么情况下需要这个功能

**建议实现**
如果有想法，描述如何实现

**替代方案**
考虑过的其他方案

**优先级**
P0/P1/P2/P3
```

### 提交代码

1. **Fork 项目**
2. **创建分支**: `git checkout -b feature/AmazingFeature`
3. **编写代码**: 遵循代码规范
4. **运行测试**: `./scripts/test.sh`
5. **提交更改**: `git commit -m 'feat: add amazing feature'`
6. **推送分支**: `git push origin feature/AmazingFeature`
7. **创建 Pull Request**

## 开发流程

### 环境设置

```bash
# 克隆项目
git clone https://github.com/yourusername/rag-pro-max.git
cd rag-pro-max

# 安装依赖
pip install -r requirements.txt

# 运行测试
./scripts/test.sh
```

### 开发循环

```bash
# 1. 创建功能分支
git checkout -b feature/my-feature

# 2. 编写代码
vim src/apppro.py

# 3. 运行测试
./scripts/test.sh

# 4. 提交更改
git add .
git commit -m "feat: add my feature"

# 5. 推送分支
git push origin feature/my-feature
```

### 测试要求

**所有代码必须通过出厂测试**:

```bash
./scripts/test.sh
```

**测试覆盖**:
- ✅ 环境检查
- ✅ 配置文件
- ✅ 核心模块
- ✅ 日志系统
- ✅ 文档处理
- ✅ 向量数据库
- ✅ LLM 连接
- ✅ 存储目录
- ✅ 安全性
- ✅ 性能配置

## 代码规范

### Python 代码风格

遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范：

```python
# 好的示例
def process_document(file_path: str, chunk_size: int = 500) -> List[Document]:
    """
    处理文档并分块
    
    Args:
        file_path: 文档路径
        chunk_size: 分块大小
        
    Returns:
        文档列表
    """
    documents = []
    # 处理逻辑
    return documents

# 避免
def proc_doc(fp,cs=500):
    docs=[]
    return docs
```

### 命名规范

- **变量**: `snake_case` (e.g. `chunk_size`, `file_path`)
- **函数**: `snake_case` (e.g. `process_document`, `load_index`)
- **类**: `PascalCase` (e.g. `DocumentProcessor`, `VectorStore`)
- **常量**: `UPPER_CASE` (e.g. `MAX_FILE_SIZE`, `DEFAULT_MODEL`)

### 注释规范

```python
# 单行注释：解释为什么这样做
chunk_size = 500  # 经过测试，500 是最优分块大小

def complex_function():
    """
    多行文档字符串：描述函数功能
    
    详细说明函数的作用、参数、返回值
    """
    pass
```

### 最小化原则

**只写必要的代码**:

```python
# 好的：简洁明了
filtered = [x for x in items if x > 0]

# 避免：过度复杂
filtered = []
for item in items:
    if item > 0:
        filtered.append(item)
```

## 提交规范

### Commit Message 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具相关

### 示例

```bash
# 新功能
git commit -m "feat(rerank): add Re-ranking support"

# Bug 修复
git commit -m "fix(security): fix subprocess injection vulnerability"

# 文档更新
git commit -m "docs(readme): update installation guide"

# 性能优化
git commit -m "perf(vector): optimize embedding batch size"
```

## Pull Request 流程

### PR 标题

使用与 Commit Message 相同的格式：

```
feat(bm25): add BM25 hybrid retrieval
```

### PR 描述模板

```markdown
## 变更类型
- [ ] 新功能
- [ ] Bug 修复
- [ ] 文档更新
- [ ] 性能优化
- [ ] 重构

## 变更说明
简要描述这个 PR 做了什么

## 测试
- [ ] 通过所有出厂测试 (./scripts/test.sh)
- [ ] 添加了新的测试（如果适用）
- [ ] 手动测试通过

## 相关 Issue
Closes #123

## 截图
如果适用，添加截图

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 添加了必要的注释
- [ ] 更新了相关文档
- [ ] 通过了所有测试
```

### Review 流程

1. **自动检查**: CI 自动运行测试
2. **代码审查**: 维护者审查代码
3. **讨论修改**: 根据反馈修改
4. **合并**: 审查通过后合并

## 文档贡献

### 文档类型

- **README.md**: 项目概述和快速开始
- **功能文档**: 详细的功能说明（如 RERANK.md）
- **开发文档**: 开发相关文档（如 CONTRIBUTING.md）
- **API 文档**: API 接口文档

### 文档规范

- 使用清晰的标题层级
- 提供代码示例
- 添加截图（如果适用）
- 保持简洁明了

## 社区

### 获取帮助

- **Issues**: 提问和讨论
- **Discussions**: 一般性讨论
- **Email**: 私密问题

### 保持联系

- 关注项目更新
- 参与讨论
- 分享使用经验

## 许可证

贡献的代码将采用与项目相同的 MIT 许可证。

---

**感谢你的贡献！** 🎉

每一个贡献，无论大小，都让 RAG Pro Max 变得更好。
