# 知识库模块使用指南

## 📚 模块概述

知识库管理模块提供了完整的知识库 CRUD 操作和高级管理功能。

### 模块结构
```
src/kb/
├── __init__.py              # 模块导出
├── kb_operations.py         # 基础操作（静态方法）
└── kb_manager.py            # 高级管理（面向对象）
```

---

## 🚀 快速开始

### 基础用法

```python
from src.kb import KBManager

# 创建管理器
manager = KBManager()

# 创建知识库
success, msg = manager.create("my_knowledge_base")
print(msg)  # ✅ 知识库 'my_knowledge_base' 创建成功

# 列出所有知识库
kbs = manager.list_all()
print(f"共有 {len(kbs)} 个知识库")

# 检查知识库是否存在
if manager.exists("my_knowledge_base"):
    print("知识库存在")
```

---

## 📖 API 文档

### KBManager 类

#### 初始化

```python
manager = KBManager(
    base_path="vector_db_storage",    # 知识库根目录
    history_dir="chat_histories"       # 对话历史目录
)
```

#### 方法列表

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `create(kb_name)` | str | (bool, str) | 创建知识库 |
| `delete(kb_name)` | str | (bool, str) | 删除知识库 |
| `rename(old, new)` | str, str | (bool, str) | 重命名知识库 |
| `list_all(sort_by_time)` | bool | List[str] | 列出所有知识库 |
| `exists(kb_name)` | str | bool | 检查是否存在 |
| `get_info(kb_name)` | str | Dict | 获取知识库信息 |
| `save_info(kb_name, model, dim)` | str, str, int | bool | 保存知识库信息 |
| `get_stats(kb_name)` | str | Dict | 获取统计信息 |
| `search(keyword)` | str | List[str] | 搜索知识库 |

---

## 💡 使用示例

### 1. 创建和管理知识库

```python
from src.kb import KBManager

manager = KBManager()

# 创建知识库
success, msg = manager.create("python_docs")
if success:
    print(msg)  # ✅ 知识库 'python_docs' 创建成功
else:
    print(f"创建失败: {msg}")

# 重命名知识库
success, msg = manager.rename("python_docs", "py_docs")
if success:
    print(msg)  # ✅ 知识库已重命名: python_docs → py_docs

# 删除知识库
success, msg = manager.delete("py_docs")
if success:
    print(msg)  # ✅ 知识库 'py_docs' 已删除
```

### 2. 查询知识库信息

```python
# 获取详细信息
info = manager.get_info("my_kb")
if info:
    print(f"名称: {info['name']}")
    print(f"路径: {info['path']}")
    print(f"模型: {info['embedding_model']}")
    print(f"维度: {info['embedding_dim']}")
    print(f"创建时间: {info['created_time']}")

# 获取统计信息
stats = manager.get_stats("my_kb")
if stats:
    print(f"大小: {manager.format_size(stats['size'])}")
    print(f"文件数: {stats['file_count']}")
    print(f"修改时间: {stats['modified_time']}")
```

### 3. 搜索和过滤

```python
# 列出所有知识库（按时间排序）
kbs = manager.list_all(sort_by_time=True)
print(f"最近使用的知识库: {kbs[0]}")

# 列出所有知识库（按名称排序）
kbs = manager.list_all(sort_by_time=False)
print(f"知识库列表: {', '.join(kbs)}")

# 搜索知识库
results = manager.search("python")
print(f"找到 {len(results)} 个包含 'python' 的知识库")
for kb in results:
    print(f"  - {kb}")
```

### 4. 保存和加载知识库信息

```python
# 保存知识库信息
success = manager.save_info(
    kb_name="my_kb",
    embed_model="BAAI/bge-small-zh-v1.5",
    embed_dim=512
)

if success:
    print("✅ 知识库信息已保存")

# 加载知识库信息
info = manager.get_info("my_kb")
if info:
    print(f"嵌入模型: {info['embedding_model']}")
    print(f"嵌入维度: {info['embedding_dim']}")
```

---

## 🔧 高级用法

### 使用 KBOperations（静态方法）

如果只需要基础操作，可以直接使用 `KBOperations`:

```python
from src.kb import KBOperations

ops = KBOperations()

# 创建知识库
ops.create_kb("test_kb", "vector_db_storage")

# 列出知识库
kbs = ops.list_kbs("vector_db_storage", sort_by_time=True)

# 检查存在
exists = ops.kb_exists("test_kb", "vector_db_storage")

# 保存信息
ops.save_kb_info(
    db_path="vector_db_storage/test_kb",
    embed_model="bge-small",
    embed_dim=512
)

# 加载信息
info = ops.load_kb_info("vector_db_storage/test_kb")
```

### 自定义路径

```python
# 使用自定义路径
manager = KBManager(
    base_path="/custom/path/to/kbs",
    history_dir="/custom/path/to/histories"
)

# 所有操作都会使用自定义路径
success, msg = manager.create("custom_kb")
```

---

## 🎯 最佳实践

### 1. 错误处理

```python
# 始终检查返回值
success, msg = manager.create("my_kb")
if not success:
    print(f"❌ 错误: {msg}")
    # 处理错误
else:
    print(f"✅ {msg}")
    # 继续操作
```

### 2. 存在性检查

```python
# 操作前先检查存在性
if manager.exists("my_kb"):
    stats = manager.get_stats("my_kb")
    # 使用统计信息
else:
    print("知识库不存在")
```

### 3. 信息持久化

```python
# 创建知识库后立即保存信息
success, msg = manager.create("new_kb")
if success:
    manager.save_info(
        kb_name="new_kb",
        embed_model="BAAI/bge-small-zh-v1.5",
        embed_dim=512
    )
```

### 4. 批量操作

```python
# 批量创建知识库
kb_names = ["kb1", "kb2", "kb3"]
for name in kb_names:
    success, msg = manager.create(name)
    if success:
        print(f"✅ {name} 创建成功")

# 批量获取统计信息
for kb in manager.list_all():
    stats = manager.get_stats(kb)
    print(f"{kb}: {manager.format_size(stats['size'])}")
```

---

## 🔄 迁移指南

### 从旧代码迁移

**旧代码** (utils/kb_manager.py):
```python
from src.utils.kb_manager import (
    rename_kb,
    get_existing_kbs,
    delete_kb,
    kb_exists
)

# 使用
rename_kb("old", "new", "path", "hist")
kbs = get_existing_kbs("path")
delete_kb("kb", "path", "hist")
exists = kb_exists("kb", "path")
```

**新代码** (kb/):
```python
from src.kb import KBManager

manager = KBManager(base_path="path", history_dir="hist")

# 使用
success, msg = manager.rename("old", "new")
kbs = manager.list_all()
success, msg = manager.delete("kb")
exists = manager.exists("kb")
```

### 优势对比

| 特性 | 旧代码 | 新代码 |
|------|--------|--------|
| 设计模式 | 函数式 | 面向对象 |
| 参数传递 | 每次都要传 | 初始化一次 |
| 返回值 | 不统一 | 统一 (bool, str) |
| 错误处理 | 分散 | 集中 |
| 功能完整性 | 基础 | 高级 |
| 可测试性 | 低 | 高 |

---

## 🧪 测试

### 运行测试

```bash
# 运行知识库模块测试
python3 tests/test_kb_modules.py

# 预期输出
✅ 通过: 15/15
❌ 失败: 0/15
✅ 所有测试通过！
```

### 测试覆盖

- ✅ 创建知识库
- ✅ 删除知识库
- ✅ 重命名知识库
- ✅ 列出知识库
- ✅ 检查存在
- ✅ 保存/加载信息
- ✅ 获取统计信息
- ✅ 搜索知识库
- ✅ 格式化大小

---

## ❓ 常见问题

### Q: 如何处理知识库名称冲突？

```python
success, msg = manager.create("existing_kb")
if not success and "已存在" in msg:
    print("知识库已存在，使用其他名称")
```

### Q: 如何获取知识库大小？

```python
stats = manager.get_stats("my_kb")
size_str = manager.format_size(stats['size'])
print(f"知识库大小: {size_str}")
```

### Q: 如何批量删除知识库？

```python
# 删除所有包含 "test" 的知识库
test_kbs = manager.search("test")
for kb in test_kbs:
    success, msg = manager.delete(kb)
    print(msg)
```

### Q: 如何备份知识库？

```python
import shutil

# 获取知识库路径
info = manager.get_info("my_kb")
if info:
    kb_path = info['path']
    backup_path = f"{kb_path}_backup"
    shutil.copytree(kb_path, backup_path)
    print(f"✅ 备份完成: {backup_path}")
```

---

## 📚 相关文档

- [Stage 9 完成报告](STAGE_9_COMPLETE.md)
- [重构进度报告](REFACTOR_PROGRESS.md)
- [测试文档](../TESTING.md)
- [API 文档](API.md)

---

*文档更新时间: 2025-12-09 13:00*
