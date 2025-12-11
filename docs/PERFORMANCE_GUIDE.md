# 性能优化指南

## 🎯 性能概览

RAG Pro Max v2.0.1 在保证系统稳定的前提下，提供了优秀的处理性能。

### 📊 基准性能

| 指标 | v1.0 | v2.0.1 | 改进 |
|------|------|--------|------|
| CPU峰值 | 100% | 85% | ↓15% |
| 系统稳定性 | 易死机 | 稳定 | ✅ |
| OCR速度 | 3页/秒 | 1.5页/秒 | 更稳定 |
| 查询延迟 | 1-3秒 | 1-2秒 | ↓33% |

## 🛡️ CPU保护机制

### 动态进程控制

```python
# CPU使用率 → 进程数映射
def get_optimal_workers(cpu_usage):
    if cpu_usage > 85:
        return 1  # 极限保护
    elif cpu_usage > 70:
        return 2  # 严格保护
    elif cpu_usage > 50:
        return 3  # 超保守模式
    else:
        return 4  # 保守高效模式
```

### 实时监控

- **监控频率**: 0.5秒
- **保护阈值**: 95%
- **紧急阈值**: 98% (连续3次)
- **自动暂停**: 3秒降温

## ⚡ 性能优化策略

### 1. 硬件优化

**推荐配置**:
- **CPU**: 8核以上 (推荐14核M4 Max)
- **内存**: 16GB以上 (推荐32GB+)
- **存储**: SSD (推荐NVMe)
- **GPU**: 可选 (MPS/CUDA加速)

**资源分配**:
```python
# 保守配置 (8核系统)
max_workers = 2
cpu_threshold = 70
batch_size = 10

# 高性能配置 (14核系统)
max_workers = 4
cpu_threshold = 85
batch_size = 20
```

### 2. 软件优化

**OCR优化**:
```python
# src/utils/ocr_optimizer.py
class OCROptimizer:
    max_cpu_usage = 85.0      # 降低CPU限制
    max_workers = 4           # 限制进程数
    timeout_minutes = 10      # 缩短超时
    emergency_threshold = 98.0 # 紧急停止
```

**批量处理优化**:
```python
# 小批量处理 (稳定优先)
batch_size = 10
concurrent_limit = 2

# 大批量处理 (效率优先)
batch_size = 30
concurrent_limit = 4
```

### 3. 内存优化

**内存管理**:
```python
# 定期清理内存
from src.utils.memory import cleanup_memory
cleanup_memory()

# 监控内存使用
import psutil
memory_percent = psutil.virtual_memory().percent
if memory_percent > 80:
    # 减少批量大小
    batch_size = max(5, batch_size // 2)
```

**GPU内存优化**:
```python
# MPS缓存清理
import torch
if torch.backends.mps.is_available():
    torch.mps.empty_cache()

# CUDA缓存清理
if torch.cuda.is_available():
    torch.cuda.empty_cache()
```

## 📈 性能监控

### 实时监控

```bash
# CPU监控脚本
#!/bin/bash
while true; do
    cpu=$(python -c "import psutil; print(f'{psutil.cpu_percent():.1f}')")
    echo "$(date '+%H:%M:%S') CPU: ${cpu}%"
    if (( $(echo "$cpu > 90" | bc -l) )); then
        echo "⚠️  CPU过高，建议暂停处理"
    fi
    sleep 2
done
```

### 性能分析

```python
# 性能分析脚本
import time
import psutil
from src.utils.ocr_optimizer import ocr_optimizer

def analyze_performance():
    start_time = time.time()
    start_cpu = psutil.cpu_percent()
    
    # 模拟OCR处理
    workers, strategy = ocr_optimizer.get_optimal_workers(20)
    
    print(f"策略: {strategy}")
    print(f"进程数: {workers}")
    print(f"预估时间: {ocr_optimizer.estimate_time(20, workers):.1f}秒")
    
    # 资源使用情况
    memory = psutil.virtual_memory()
    print(f"内存使用: {memory.percent:.1f}%")
    print(f"可用内存: {memory.available/1024/1024/1024:.1f}GB")
```

## 🔧 配置调优

### 基础配置

```json
// config/performance.json
{
  "ocr": {
    "max_workers": 4,
    "cpu_threshold": 85,
    "timeout_minutes": 10,
    "batch_size": 20
  },
  "memory": {
    "cleanup_interval": 300,
    "warning_threshold": 80,
    "critical_threshold": 90
  },
  "monitoring": {
    "interval": 0.5,
    "emergency_threshold": 98,
    "consecutive_limit": 3
  }
}
```

### 环境变量

```bash
# 性能相关环境变量
export RAG_MAX_WORKERS=4
export RAG_CPU_THRESHOLD=85
export RAG_BATCH_SIZE=20
export RAG_TIMEOUT=600
export RAG_MONITOR_INTERVAL=0.5
```

### 动态调整

```python
# 运行时动态调整
def adjust_performance(cpu_usage, memory_usage):
    if cpu_usage > 90 or memory_usage > 85:
        # 紧急模式
        return {
            'max_workers': 1,
            'batch_size': 5,
            'timeout': 300
        }
    elif cpu_usage > 70 or memory_usage > 70:
        # 保守模式
        return {
            'max_workers': 2,
            'batch_size': 10,
            'timeout': 600
        }
    else:
        # 正常模式
        return {
            'max_workers': 4,
            'batch_size': 20,
            'timeout': 600
        }
```

## 📊 性能测试

### 基准测试

```python
# 性能基准测试
import time
from src.utils.batch_ocr_processor import BatchOCRProcessor

def benchmark_ocr():
    processor = BatchOCRProcessor()
    
    # 测试不同页数的处理时间
    test_cases = [5, 10, 20, 50]
    
    for pages in test_cases:
        start_time = time.time()
        
        # 模拟OCR处理
        # ... 处理逻辑 ...
        
        elapsed = time.time() - start_time
        pages_per_sec = pages / elapsed
        
        print(f"{pages}页: {elapsed:.1f}秒, {pages_per_sec:.2f}页/秒")
```

### 压力测试

```bash
# 压力测试脚本
#!/bin/bash
echo "开始压力测试..."

# 监控CPU和内存
python -c "
import psutil
import time

for i in range(60):  # 监控1分钟
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    
    print(f'第{i+1}秒: CPU {cpu:.1f}%, Memory {memory:.1f}%')
    
    if cpu > 95:
        print('⚠️  CPU过载！')
        break
    if memory > 90:
        print('⚠️  内存不足！')
        break
"
```

## 🎯 优化建议

### 日常使用

1. **分批处理**: 大量文档分批上传，每批10-20个文件
2. **定期清理**: 每天清理临时文件和缓存
3. **监控资源**: 定期检查CPU和内存使用率
4. **合理配置**: 根据硬件性能调整参数

### 高负载场景

1. **降低并发**: 减少同时处理的文档数量
2. **增加间隔**: 在批次之间添加休息时间
3. **监控温度**: 注意CPU温度，必要时暂停
4. **备用方案**: 准备紧急停止脚本

### 性能调优

```python
# 自适应性能调优
class AdaptiveOptimizer:
    def __init__(self):
        self.performance_history = []
        
    def adjust_settings(self):
        current_performance = self.measure_performance()
        
        if current_performance < 0.5:  # 性能较差
            return {
                'max_workers': 1,
                'batch_size': 5,
                'aggressive': False
            }
        elif current_performance > 0.8:  # 性能良好
            return {
                'max_workers': 4,
                'batch_size': 30,
                'aggressive': True
            }
        else:  # 性能中等
            return {
                'max_workers': 2,
                'batch_size': 15,
                'aggressive': False
            }
```

## 🚨 故障预防

### 预警机制

```python
# 性能预警
def performance_warning():
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    
    warnings = []
    
    if cpu > 80:
        warnings.append(f"CPU使用率较高: {cpu:.1f}%")
    if memory > 75:
        warnings.append(f"内存使用率较高: {memory:.1f}%")
    
    if warnings:
        print("⚠️  性能警告:")
        for warning in warnings:
            print(f"  - {warning}")
        
        return True
    return False
```

### 自动恢复

```python
# 自动性能恢复
def auto_recovery():
    if performance_warning():
        print("🔄 启动自动恢复...")
        
        # 清理内存
        cleanup_memory()
        
        # 降低处理强度
        ocr_optimizer.max_workers = 1
        
        # 等待系统恢复
        time.sleep(10)
        
        print("✅ 自动恢复完成")
```

## 📈 性能报告

### 生成报告

```python
# 性能报告生成器
def generate_performance_report():
    report = {
        'timestamp': time.time(),
        'system': {
            'cpu_cores': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'platform': platform.platform()
        },
        'current_usage': {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent
        },
        'ocr_settings': {
            'max_workers': ocr_optimizer.max_workers,
            'cpu_threshold': ocr_optimizer.max_cpu_usage
        }
    }
    
    return report
```

通过这些优化策略和监控机制，RAG Pro Max v2.0.1 能够在保证系统稳定的前提下，提供最佳的处理性能。
