# Stage 6 多进程/并行执行重构计划

## 📋 现状分析

### 当前并行执行位置

#### 1. 元数据提取（IndexBuilder）
```python
# src/processors/index_builder.py:233
with mp.Pool(processes=num_workers) as pool:
    results = pool.map(_extract_metadata_task, tasks, chunksize=50)
```
- **触发条件**: 文件数 > 100
- **进程数**: min(cpu_count, 12)
- **问题**: 
  - 阈值100太高，中小型知识库无法利用
  - 使用 `mp.Pool` 而非 `ProcessPoolExecutor`（不统一）
  - `_extract_metadata_task` 在主文件中定义（apppro.py:186）

#### 2. 问答节点处理（主文件）
```python
# src/apppro.py:2417
with ProcessPoolExecutor(max_workers=max_workers) as executor:
    srcs = [s for s in executor.map(_process_node_worker, 
           [(d, active_kb_name) for d in node_data]) if s]
```
- **触发条件**: 节点数 > 20
- **进程数**: max(2, min(cpu_count-1, len(node_data)//2))
- **问题**:
  - `_process_node_worker` 在主文件中定义（apppro.py:165）
  - 阈值20可能仍然偏高

#### 3. 摘要生成（IndexBuilder）
```python
# src/processors/index_builder.py:271
thread = threading.Thread(target=write_queue_async, daemon=True)
thread.start()
```
- **方式**: 异步线程
- **状态**: ✅ 已优化（Stage 5.2）

---

## 🎯 存在的问题

### 1. 代码分散
- 多进程函数定义在主文件（apppro.py）
- 不利于维护和测试
- 违反模块化原则

### 2. 不统一
- 混用 `mp.Pool` 和 `ProcessPoolExecutor`
- 阈值不一致（100 vs 20）
- 进程数计算逻辑不统一

### 3. 阈值不合理
- 元数据提取: 100个文件才启用（太高）
- 节点处理: 20个节点才启用（可能偏高）
- 缺少动态调整机制

### 4. 缺少统一管理
- 没有并行执行管理器
- 没有资源池复用
- 每次都创建新进程池（开销大）

---

## 🚀 重构目标

### 1. 提取并行执行模块
创建 `src/utils/parallel_executor.py`：
- 统一的并行执行接口
- 智能阈值判断
- 进程池复用
- 资源监控

### 2. 优化阈值策略
- **元数据提取**: 50个文件启用（降低50%）
- **节点处理**: 10个节点启用（降低50%）
- **动态调整**: 根据CPU核心数和负载动态调整

### 3. 统一并行方式
- 全部使用 `ProcessPoolExecutor`（更现代）
- 统一进程数计算逻辑
- 统一错误处理

### 4. 进程池复用
- 创建全局进程池
- 避免重复创建销毁
- 提升性能 5-10%

---

## 📊 预期效果

### 性能提升
| 场景 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| 中型知识库（50-100文件） | 无并行 | 并行 | 30-40% |
| 大型知识库（>100文件） | 并行 | 优化并行 | 10-15% |
| 问答节点处理（10-20节点） | 无并行 | 并行 | 20-30% |

### 代码质量
- ✅ 模块化：并行逻辑独立
- ✅ 可测试：单元测试覆盖
- ✅ 可维护：统一接口
- ✅ 可扩展：易于添加新场景

---

## 🔧 实施计划

### Phase 1: 提取并行执行模块（2小时）
1. 创建 `src/utils/parallel_executor.py`
2. 实现 `ParallelExecutor` 类
3. 实现智能阈值判断
4. 实现进程池管理

### Phase 2: 重构元数据提取（1小时）
1. 移动 `_extract_metadata_task` 到新模块
2. 使用 `ParallelExecutor` 替换 `mp.Pool`
3. 降低阈值到50
4. 添加单元测试

### Phase 3: 重构节点处理（1小时）
1. 移动 `_process_node_worker` 到新模块
2. 使用 `ParallelExecutor` 统一接口
3. 优化阈值判断
4. 添加单元测试

### Phase 4: 进程池复用（1小时）
1. 实现全局进程池
2. 生命周期管理
3. 资源清理
4. 性能测试

### Phase 5: 测试和文档（1小时）
1. 单元测试
2. 集成测试
3. 性能对比测试
4. 更新文档

**总计**: 6小时

---

## 📝 实施细节

### ParallelExecutor 设计

```python
class ParallelExecutor:
    """统一的并行执行管理器"""
    
    def __init__(self, max_workers=None):
        self.max_workers = max_workers or (os.cpu_count() - 1)
        self._executor = None
    
    def should_parallelize(self, task_count: int, threshold: int = 10) -> bool:
        """智能判断是否需要并行"""
        # 任务数太少，串行更快
        if task_count < threshold:
            return False
        
        # CPU核心数太少，并行无意义
        if os.cpu_count() <= 2:
            return False
        
        # 资源占用过高，避免并行
        cpu_percent = psutil.cpu_percent(interval=0.1)
        if cpu_percent > 80:
            return False
        
        return True
    
    def execute(self, func, tasks, chunksize=None):
        """执行并行任务"""
        if not self.should_parallelize(len(tasks)):
            # 串行执行
            return [func(task) for task in tasks]
        
        # 并行执行
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            return list(executor.map(func, tasks, chunksize=chunksize))
    
    def execute_with_progress(self, func, tasks, callback=None):
        """带进度的并行执行"""
        if not self.should_parallelize(len(tasks)):
            results = []
            for i, task in enumerate(tasks):
                results.append(func(task))
                if callback:
                    callback(i + 1, len(tasks))
            return results
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(func, task): i for i, task in enumerate(tasks)}
            results = [None] * len(tasks)
            
            for future in as_completed(futures):
                idx = futures[future]
                results[idx] = future.result()
                if callback:
                    callback(idx + 1, len(tasks))
            
            return results
```

### 使用示例

```python
# 元数据提取
executor = ParallelExecutor()
results = executor.execute(_extract_metadata_task, tasks, chunksize=50)

# 节点处理
executor = ParallelExecutor(max_workers=8)
srcs = executor.execute(_process_node_worker, node_data)
```

---

## 🧪 测试计划

### 单元测试
- `test_parallel_executor.py`: 并行执行器测试
- `test_threshold_logic.py`: 阈值判断测试
- `test_pool_reuse.py`: 进程池复用测试

### 性能测试
- 对比串行 vs 并行
- 对比优化前 vs 优化后
- 不同任务数的性能曲线

### 集成测试
- 元数据提取集成测试
- 节点处理集成测试
- 端到端测试

---

## 📈 优先级评估

### 高优先级 ⭐⭐⭐
- **提取并行执行模块**: 代码质量提升
- **降低阈值**: 中小型知识库性能提升 30-40%

### 中优先级 ⭐⭐
- **统一并行方式**: 代码一致性
- **进程池复用**: 性能提升 5-10%

### 低优先级 ⭐
- **动态调整**: 边际收益较小
- **资源监控**: 已有基础监控

---

## 🎯 建议

### 立即实施
1. **Phase 1-3**: 提取模块 + 重构（4小时）
   - 代码质量立即提升
   - 中小型知识库性能提升 30-40%
   - 为后续优化打基础

### 后续实施
2. **Phase 4-5**: 进程池复用 + 测试（2小时）
   - 进一步提升性能 5-10%
   - 完善测试覆盖

---

## 📚 相关文档

- [Stage 5 性能优化总结](STAGE5_SUMMARY.md)
- [重构总结](REFACTOR_SUMMARY.md)

---

*计划创建时间: 2025-12-09*
*预计完成时间: 6小时*
