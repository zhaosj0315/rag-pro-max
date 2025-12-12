# 资源保护机制 v2.0 - 防止系统死机

## 📋 优化概述

基于用户反馈，进一步降低资源使用阈值，增强系统稳定性保护。

## 🎯 优化目标

- 降低20%的资源使用率
- 防止电脑死机
- 增加内存保护机制
- 保持处理效率

## 📊 阈值调整

### CPU使用率
- **原阈值**: 95%
- **新阈值**: 75% (-20%)
- **保护级别**: 更加保守

### 内存使用率
- **原阈值**: 90%
- **新阈值**: 85% (-5%)
- **监控方式**: 实时监控

### 工作进程数
- **原设置**: 4个进程
- **新设置**: 3个进程 (-25%)
- **调整策略**: 动态调节

## 🔧 技术实现

### 1. 资源监控器升级

```python
class ResourceLimiter:
    def __init__(self, max_cpu_percent: float = 75.0, max_memory_percent: float = 85.0):
        self.max_cpu_percent = max_cpu_percent
        self.max_memory_percent = max_memory_percent
```

### 2. 动态线程调整

```python
def get_safe_worker_count(self, default_workers: int) -> int:
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_percent = psutil.virtual_memory().percent
    
    # 综合考虑CPU和内存使用率
    max_usage = max(cpu_percent, memory_percent)
    
    if max_usage > 70:
        return max(1, default_workers // 4)  # 高负载时减少到1/4
    elif max_usage > 60:
        return max(2, default_workers // 2)  # 中等负载时减少到1/2
    elif max_usage > 50:
        return max(3, default_workers * 3 // 4)  # 轻微负载时减少到3/4
    else:
        return default_workers  # 低负载时使用默认值
```

### 3. OCR处理器优化

```python
class OptimizedOCRProcessor:
    def __init__(self):
        self.resource_limiter = get_resource_limiter(max_cpu_percent=75.0, max_memory_percent=85.0)
        self.max_workers = 3  # 降低最大进程数
```

## 📈 优化效果

### 资源使用对比

| 项目 | 原设置 | 新设置 | 变化 |
|------|--------|--------|------|
| CPU阈值 | 95% | 75% | -20% |
| 内存阈值 | 90% | 85% | -5% |
| 最大进程 | 4个 | 3个 | -25% |
| 监控维度 | CPU | CPU+内存 | +100% |

### 保护机制

- ✅ **双重保护**: CPU + 内存同时监控
- ✅ **动态调节**: 根据实际负载智能调整
- ✅ **提前预警**: 更低的阈值，更早的保护
- ✅ **系统稳定**: 防止资源耗尽导致死机

## 🧪 测试验证

运行测试脚本验证优化效果：

```bash
python test_resource_limits.py
```

### 测试结果

```
📊 当前系统资源状态:
   CPU使用率: 14.0%
   内存使用率: 30.0%
   CPU过高: 否 (阈值: 75%)
   内存过高: 否 (阈值: 85%)

🔧 测试资源限制器:
   CPU阈值: 75.0%
   内存阈值: 85.0%

🔍 测试OCR处理器配置:
   最大工作进程: 3
   CPU阈值: 75.0%
   内存阈值: 85.0%
```

## 🚀 使用方式

### 自动应用

所有优化自动生效，无需手动配置：

- OCR处理自动使用新阈值
- 资源监控自动启用双重保护
- 工作线程数自动动态调整

### 手动调整

如需进一步调整，可修改参数：

```python
# 更保守的设置
limiter = get_resource_limiter(max_cpu_percent=60.0, max_memory_percent=80.0)

# 更激进的设置
limiter = get_resource_limiter(max_cpu_percent=80.0, max_memory_percent=90.0)
```

## 📝 注意事项

1. **性能影响**: 阈值降低可能略微影响处理速度
2. **系统稳定**: 大幅提升系统稳定性，避免死机
3. **向后兼容**: 完全兼容现有代码
4. **实时调整**: 系统会根据实际负载动态调整

## 🔮 未来优化

- 🎯 **预测性调度**: 基于历史数据预测资源需求
- 📊 **智能学习**: 学习用户使用模式，优化阈值
- 🔄 **自适应调整**: 根据硬件配置自动调整参数
- 📱 **用户控制**: 提供用户自定义阈值界面

---

**✅ 资源保护机制 v2.0 已完成，系统更加稳定安全！**
