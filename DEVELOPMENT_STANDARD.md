# RAG Pro Max 开发规范标准
**版本**: v2.6.1  
**更新日期**: 2025-12-19


## 🎯 核心原则
**标准化开发 - 确保代码质量、文档同步、安全合规的开发流程**

---

## 📋 开发流程规范

### 🚀 开发启动阶段

#### 1. 环境准备
```bash
# 检查开发环境
python --version  # 确保 Python 3.8+
git --version     # 确保 Git 可用

# 安装依赖
pip install -r requirements.txt

# 运行基础测试
python tests/factory_test.py --quick
```

#### 2. 分支管理
```bash
# 从主分支创建功能分支
git checkout main
git pull origin main
git checkout -b feature/功能名称

# 分支命名规范
feature/新功能名称     # 新功能开发
fix/问题描述          # Bug修复  
refactor/重构内容     # 代码重构
docs/文档更新         # 文档更新
```

### 🔧 开发过程规范

#### 代码开发标准
```python
# 1. 文件头注释
"""
RAG Pro Max - 模块名称
功能描述: 简要说明模块功能
作者: 开发者名称
创建时间: YYYY-MM-DD
"""

# 2. 函数注释
def function_name(param1: str, param2: int) -> bool:
    """
    函数功能描述
    
    Args:
        param1: 参数1说明
        param2: 参数2说明
        
    Returns:
        返回值说明
        
    Raises:
        异常说明
    """
    pass

# 3. 类注释
class ClassName:
    """
    类功能描述
    
    Attributes:
        attr1: 属性1说明
        attr2: 属性2说明
    """
    pass
```

#### 代码质量要求
- ✅ **PEP 8 规范**: 遵循Python代码风格
- ✅ **类型注解**: 重要函数添加类型提示
- ✅ **异常处理**: 合理的try-catch结构
- ✅ **日志记录**: 关键操作添加日志
- ✅ **性能考虑**: 避免明显的性能问题

### 📝 文档同步规范

#### 开发过程中必须同步的文档
```bash
# 每次功能开发完成后检查
python scripts/check_documentation_sync.py

# 需要同步的文档
- README.md          # 新功能说明
- CHANGELOG.md       # 版本变更记录
- API.md            # 新增API接口
- USER_MANUAL.md     # 使用说明更新
- FAQ.md            # 新问题解答
```

#### 文档更新标准
- ✅ **及时更新**: 功能完成立即更新文档
- ✅ **内容准确**: 文档与代码实现一致
- ✅ **用户友好**: 使用简洁易懂的语言
- ✅ **示例完整**: 提供完整的使用示例

### 🧪 测试规范

#### 测试要求
```bash
# 开发过程中的测试
python tests/factory_test.py          # 完整测试
python tests/factory_test.py --quick  # 快速测试

# 测试覆盖率要求
- 核心功能: 100%覆盖
- 工具函数: 90%+覆盖  
- UI组件: 80%+覆盖
- 总体覆盖率: 85%+
```

#### 测试类型
- ✅ **单元测试**: 测试单个函数/类
- ✅ **集成测试**: 测试模块间交互
- ✅ **功能测试**: 测试完整功能流程
- ✅ **性能测试**: 测试关键性能指标

---

## 🔒 安全开发规范

### 代码安全
```python
# 1. 敏感信息处理
# ❌ 错误做法
api_key = "sk-1234567890abcdef"

# ✅ 正确做法  
api_key = os.getenv("API_KEY", "")
if not api_key:
    raise ValueError("API_KEY environment variable not set")

# 2. 输入验证
def process_file(file_path: str):
    # 验证文件路径
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # 验证文件类型
    allowed_extensions = ['.pdf', '.txt', '.docx']
    if not any(file_path.endswith(ext) for ext in allowed_extensions):
        raise ValueError(f"Unsupported file type: {file_path}")
```

### 数据安全
- ✅ **用户数据**: 本地存储，不推送远程
- ✅ **配置文件**: 敏感配置使用环境变量
- ✅ **日志安全**: 不记录敏感信息
- ✅ **文件权限**: 合理设置文件访问权限

### 依赖安全
```bash
# 定期检查依赖安全
pip audit

# 更新依赖版本
pip list --outdated
pip install --upgrade package_name
```

---

## 📊 版本管理规范

### 版本号规范
```json
// version.json
{
    "version": "2.4.4",
    "build": "20251217",
    "stage": "production"
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
- [API文档](API.md)
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
