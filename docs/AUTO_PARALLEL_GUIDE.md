# 自动并行执行指南

## 📋 概述

`ParallelExecutor` 提供了三种使用方式：
1. **手动调用**：完全控制
2. **便捷函数**：简化调用
3. **装饰器**：自动应用（未来）

---

## 🚀 使用方式

### 方式1: 手动调用（当前推荐）

**适用场景**: 需要完全控制并行行为

```python
from src.utils.parallel_executor import ParallelExecutor
from src.utils.parallel_tasks import extract_metadata_task

# 创建执行器
executor = ParallelExecutor()

# 准备任务
tasks = [(file1, name1, ids1, text1, dir1),
         (file2, name2, ids2, text2, dir2),
         ...]

# 执行（自动判断串行/并行）
results = executor.execute(
    extract_metadata_task, 
    tasks, 
    chunksize=50,    # 可选
    threshold=50     # 少于50个任务时串行
)
```

**优点**:
- ✅ 完全控制
- ✅ 灵活配置
- ✅ 易于调试

---

### 方式2: 便捷函数（推荐）

**适用场景**: 简单的列表处理

```python
from src.utils.parallel_executor import parallelize_list

def process_single_file(file_path):
    """处理单个文件"""
    # 处理逻辑
    return result

# 自动并行处理文件列表
file_list = ['file1.txt', 'file2.txt', ...]
results = parallelize_list(
    process_single_file, 
    file_list, 
    threshold=50
)
```

**优点**:
- ✅ 简洁易用
- ✅ 自动判断
- ✅ 一行代码

---

### 方式3: 装饰器（实验性）

**适用场景**: 函数级别的自动并行

```python
from src.utils.parallel_executor import auto_parallel

@auto_parallel(threshold=50)
def process_files(file_list):
    """处理文件列表"""
    results = []
    for file in file_list:
        results.append(process_single_file(file))
    return results

# 自动应用并行
results = process_files(large_file_list)
```

**注意**: 
- ⚠️ 装饰器目前是实验性功能
- ⚠️ 需要函数支持单元素处理
- ⚠️ 建议使用方式1或2

---

## 🎯 智能判断逻辑

### 自动判断条件

```python
def should_parallelize(task_count, threshold=10):
    # 1. 任务数检查
    if task_count < threshold:
        return False  # 太少，串行更快
    
    # 2. CPU核心数检查
    if os.cpu_count() <= 2:
        return False  # 核心太少，并行无意义
    
    # 3. CPU负载检查
    if psutil.cpu_percent() > 85:
        return False  # 负载过高，避免过载
    
    return True  # 可以并行
```

### 判断流程图

```
输入任务列表
    ↓
任务数 < threshold? ──Yes→ 串行执行
    ↓ No
CPU核心数 <= 2? ──Yes→ 串行执行
    ↓ No
CPU负载 > 85%? ──Yes→ 串行执行
    ↓ No
并行执行
```

---

## 📊 阈值配置建议

### 不同场景的阈值

| 场景 | 推荐阈值 | 理由 |
|------|---------|------|
| 元数据提取 | 50 | 单个任务耗时较长 |
| 节点处理 | 10 | 单个任务很快 |
| 文档解析 | 20 | 中等耗时 |
| 向量化 | 100 | GPU密集型，进程开销大 |

### 如何选择阈值

```python
# 经验公式
threshold = max(10, 进程创建时间 / 单任务处理时间 * 2)

# 示例
# 进程创建: 0.5s
# 单任务处理: 0.1s
# threshold = max(10, 0.5 / 0.1 * 2) = 10

# 进程创建: 0.5s
# 单任务处理: 0.01s
# threshold = max(10, 0.5 / 0.01 * 2) = 100
```

---

## 🔧 实际应用示例

### 示例1: 元数据提取（IndexBuilder）

```python
# src/processors/index_builder.py

from src.utils.parallel_executor import ParallelExecutor
from src.utils.parallel_tasks import extract_metadata_task

def _extract_metadata(self, file_map, text_samples, source_path, callback):
    # 准备任务
    tasks = []
    for fname, text in text_samples.items():
        if fname in file_map:
            fp = os.path.join(source_path, fname)
            if os.path.exists(fp):
                doc_ids = file_map[fname]['doc_ids']
                tasks.append((fp, fname, doc_ids, text, self.persist_dir))
    
    # 自动并行执行
    executor = ParallelExecutor()
    results = executor.execute(
        extract_metadata_task, 
        tasks, 
        chunksize=50, 
        threshold=50  # 50个文件以上才并行
    )
    
    # 处理结果
    for fname, meta in results:
        if fname in file_map:
            file_map[fname].update(meta)
```

### 示例2: 节点处理（主文件）

```python
# src/apppro.py

from src.utils.parallel_executor import ParallelExecutor
from src.utils.parallel_tasks import process_node_worker

# 提取节点数据
node_data = [...]

# 自动并行处理
executor = ParallelExecutor()
tasks = [(d, active_kb_name) for d in node_data]
srcs = [s for s in executor.execute(
    process_node_worker, 
    tasks, 
    threshold=10  # 10个节点以上才并行
) if s]
```

### 示例3: 便捷函数方式

```python
from src.utils.parallel_executor import parallelize_list

def process_document(doc):
    """处理单个文档"""
    # 解析、清理、提取等
    return processed_doc

# 批量处理
documents = [doc1, doc2, doc3, ...]
results = parallelize_list(
    process_document, 
    documents, 
    threshold=20
)
```

---

## ⚙️ 高级配置

### 自定义执行器

```python
# 创建自定义执行器
executor = ParallelExecutor(max_workers=8)

# 使用自定义执行器
results = executor.execute(func, tasks)
```

### 带进度回调

```python
def progress_callback(completed, total):
    print(f"进度: {completed}/{total} ({completed/total*100:.1f}%)")

executor = ParallelExecutor()
results = executor.execute_with_progress(
    func, 
    tasks, 
    callback=progress_callback,
    threshold=50
)
```

### 全局单例模式

```python
from src.utils.parallel_executor import get_global_executor

# 获取全局执行器（单例）
executor = get_global_executor()

# 所有地方使用同一个执行器
results1 = executor.execute(func1, tasks1)
results2 = executor.execute(func2, tasks2)
```

---

## 🐛 常见问题

### Q1: 为什么没有并行执行？

**可能原因**:
1. 任务数 < threshold
2. CPU核心数 <= 2
3. CPU负载 > 85%

**解决方案**:
```python
# 检查判断逻辑
executor = ParallelExecutor()
print(f"任务数: {len(tasks)}")
print(f"阈值: {threshold}")
print(f"CPU核心数: {os.cpu_count()}")
print(f"CPU负载: {psutil.cpu_percent()}%")
print(f"应该并行: {executor.should_parallelize(len(tasks), threshold)}")
```

### Q2: 如何强制并行？

```python
# 方式1: 降低阈值
results = executor.execute(func, tasks, threshold=1)

# 方式2: 直接使用 ProcessPoolExecutor
from concurrent.futures import ProcessPoolExecutor
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(func, tasks))
```

### Q3: 如何禁用并行？

```python
# 方式1: 提高阈值
results = executor.execute(func, tasks, threshold=999999)

# 方式2: 直接串行
results = [func(task) for task in tasks]
```

---

## 📈 性能对比

### 测试场景: 处理100个文件

| 方式 | 耗时 | 提升 |
|------|------|------|
| 串行 | 10.0s | - |
| 并行（2进程） | 5.5s | 45% |
| 并行（4进程） | 3.2s | 68% |
| 并行（8进程） | 2.1s | 79% |
| 并行（14进程） | 1.8s | 82% |

**结论**: 
- 并行收益明显（82%提升）
- 进程数增加收益递减
- 最优进程数约为 CPU核心数-1

---

## 🎯 最佳实践

### 1. 选择合适的阈值
```python
# 根据任务耗时选择
if 单任务耗时 > 1s:
    threshold = 10  # 低阈值
elif 单任务耗时 > 0.1s:
    threshold = 50  # 中阈值
else:
    threshold = 100  # 高阈值
```

### 2. 使用便捷函数
```python
# 推荐：简洁易用
results = parallelize_list(func, items, threshold=50)

# 不推荐：冗长
executor = ParallelExecutor()
results = executor.execute(func, items, threshold=50)
```

### 3. 避免过度并行
```python
# 不好：阈值太低，频繁创建进程
results = executor.execute(func, tasks, threshold=1)

# 好：合理阈值
results = executor.execute(func, tasks, threshold=50)
```

### 4. 监控资源使用
```python
import psutil

# 执行前检查
cpu_before = psutil.cpu_percent()
mem_before = psutil.virtual_memory().percent

results = executor.execute(func, tasks)

# 执行后检查
cpu_after = psutil.cpu_percent()
mem_after = psutil.virtual_memory().percent

print(f"CPU: {cpu_before}% → {cpu_after}%")
print(f"内存: {mem_before}% → {mem_after}%")
```

---

## 📚 相关文档

- [Stage 6 完成报告](STAGE6_COMPLETE.md)
- [并行任务函数](../src/utils/parallel_tasks.py)

---

*文档更新时间: 2025-12-09*
