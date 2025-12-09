# 资源利用率核查报告

## 核查时间
2025-12-09 08:05

## 核查目标
确保所有多进程/多线程环节的 CPU/GPU/内存利用率不超过 90%

---

## 核查结果

### ✅ 1. 文档读取阶段（多线程）
**位置**: `apppro.py` 行 1360-1450

**当前配置**:
- 目标资源使用: **80%** ✅
- 线程数动态调整: 20-80 个线程
- 资源检查: 每 5 批检查一次
- 限流阈值: **90%** ✅

**代码片段**:
```python
# 目标：保持总资源使用在80%以内
target_usage = 80.0
available_cpu = max(10, target_usage - current_cpu)

# 检查资源使用，超过90%则暂停
cpu, mem, gpu, should_throttle = check_resource_usage()
if should_throttle:  # 默认阈值 80%
    terminal_logger.warning(f"⚠️  资源使用过高...")
    time_module.sleep(1)
```

**问题**: 
- `check_resource_usage()` 默认阈值是 80%，但注释说"超过90%"
- 实际限流在 80%，不是 90%

**建议**: 统一阈值为 90%

---

### ⚠️ 2. GPU 向量化阶段
**位置**: `apppro.py` 行 1467-1580

**当前配置**:
- 目标 GPU 利用率: **<90%** ✅
- batch_size: 10000-50000（动态调整）
- 限流阈值: **90%** ✅

**代码片段**:
```python
terminal_logger.info(f"   🎯 目标: 最大化 GPU 利用率 (<90%)")

# 检查资源
if mem_percent > 90 or cpu_percent > 90 or gpu_percent > 90:
    vector_progress.write(f"      ⏸️  资源使用过高...")
    time_module.sleep(2)
```

**状态**: ✅ 已正确设置 90% 阈值

---

### ✅ 3. 元数据提取阶段（多进程）
**位置**: `apppro.py` 行 3040-3110

**当前配置**:
- 进程数: `os.cpu_count() - 1`（保留1核）
- 智能调度: >10 个节点才用多进程
- 资源监控: 查询前后记录峰值

**代码片段**:
```python
max_workers = max(2, os.cpu_count() - 1)  # 保留1核给系统

# 智能多进程处理
if len(node_data) > 10:
    max_workers = max(2, min(os.cpu_count() - 1, len(node_data) // 2))
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        srcs = [s for s in executor.map(_process_node_worker, ...)]
```

**状态**: ✅ 已保留系统资源

---

### ⚠️ 4. 资源监控模块
**位置**: `src/utils/resource_monitor.py`

**当前配置**:
- 默认阈值: **80%** ⚠️
- 可自定义阈值

**代码片段**:
```python
def check_resource_usage(threshold=80.0):
    """检查系统资源使用率"""
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory().percent
    gpu = 0.0
    
    should_throttle = cpu > threshold or mem > threshold or gpu > threshold
    return cpu, mem, gpu, should_throttle
```

**问题**: 默认阈值 80%，与目标 90% 不一致

---

## 问题汇总

| 环节 | 当前阈值 | 目标阈值 | 状态 |
|------|---------|---------|------|
| 文档读取（多线程） | 80% | 90% | ⚠️ 需修改 |
| GPU 向量化 | 90% | 90% | ✅ 正确 |
| 元数据提取（多进程） | 无限流 | 90% | ⚠️ 建议添加 |
| 资源监控默认值 | 80% | 90% | ⚠️ 需修改 |

---

## 修复建议

### 1. 统一资源监控默认阈值
**文件**: `src/utils/resource_monitor.py`

```python
# 修改前
def check_resource_usage(threshold=80.0):

# 修改后
def check_resource_usage(threshold=90.0):
```

### 2. 文档读取阶段调整目标
**文件**: `src/apppro.py` 行 1372

```python
# 修改前
target_usage = 80.0

# 修改后
target_usage = 90.0  # 允许更激进的资源使用
```

### 3. 文档读取限流阈值调整
**文件**: `src/apppro.py` 行 1441

```python
# 修改前
cpu, mem, gpu, should_throttle = check_resource_usage()  # 默认80%

# 修改后
cpu, mem, gpu, should_throttle = check_resource_usage(threshold=90.0)
```

### 4. 元数据提取添加资源监控（可选）
**文件**: `src/apppro.py` 行 3080

```python
# 在多进程处理前添加
cpu_before = psutil.cpu_percent()
if cpu_before > 90:
    terminal_logger.warning("⚠️ CPU 使用率过高，延迟元数据提取...")
    time.sleep(1)
```

---

## 验证清单

- [ ] 修改 `resource_monitor.py` 默认阈值 → 90%
- [ ] 修改文档读取目标 → 90%
- [ ] 修改文档读取限流调用 → 90%
- [ ] 运行出厂测试验证
- [ ] 实际测试大文件处理
- [ ] 监控资源峰值不超过 90%

---

## 风险评估

### 提高到 90% 的影响
- ✅ **优点**: 更充分利用硬件资源，处理速度更快
- ⚠️ **风险**: 系统响应可能变慢，其他应用受影响
- 💡 **建议**: 保持 90% 阈值，但添加更频繁的检查（每批而非每5批）

### 保守方案（如果系统不稳定）
- 保持 80% 阈值
- 添加自适应调整：空闲时 90%，繁忙时 80%
