# CPU保护机制 v2.0 - 完整文档

## 概述

RAG Pro Max v2.0 集成了全面的CPU保护机制，确保OCR处理高效但不会导致系统死机。

## 🛡️ 保护特性

### 1. 动态进程数控制

```python
# CPU使用率 → 进程数映射
CPU > 85%  → 1进程 (极限保护)
CPU 70-85% → 2进程 (严格保护)  
CPU 50-70% → 3进程 (超保守模式)
CPU < 50%  → 最多4进程 (保守高效)
```

### 2. 实时CPU监控

- **监控间隔**: 0.5秒
- **保护阈值**: 95%
- **紧急阈值**: 98% (连续3次触发停止)
- **自动暂停**: CPU过高时暂停3秒

### 3. 紧急停止机制

```bash
# 手动紧急停止
python emergency_cpu_stop.py

# 自动紧急停止条件
- 连续3次检测到CPU > 98%
- OCR进程超时(10分钟)
- 系统内存不足
```

## 📊 性能优化

### OCR处理策略

| CPU使用率 | 进程数 | 策略 | 预期性能 |
|-----------|--------|------|----------|
| < 20% | 3-4 | 保守高效 | 2-3页/秒 |
| 20-50% | 2-3 | 超保守 | 1-2页/秒 |
| 50-85% | 2 | 严格保护 | 0.5-1页/秒 |
| > 85% | 1 | 极限保护 | 0.2-0.5页/秒 |

### 资源保护

- **CPU核心保留**: 保留10-12核给系统
- **内存保护**: >70%时限制进程数
- **超时保护**: 10分钟自动终止
- **临时文件**: 自动清理

## 🔧 配置参数

### OCR优化器配置

```python
class OCROptimizer:
    max_cpu_usage = 95.0      # CPU使用率上限
    emergency_threshold = 98.0 # 紧急停止阈值
    max_workers = 4           # 最大进程数
    timeout_minutes = 10      # 超时时间
    monitor_interval = 0.5    # 监控间隔(秒)
```

### 批量处理配置

```python
# 批量OCR处理器设置
batch_size = 20           # 每批处理页数
max_concurrent = 4        # 最大并发进程
memory_limit = 70         # 内存使用率限制(%)
```

## 🚨 故障排除

### 常见问题

1. **CPU仍然过高**
   ```bash
   # 立即停止所有OCR进程
   python emergency_cpu_stop.py
   
   # 重启应用
   ./start.sh
   ```

2. **OCR处理缓慢**
   ```bash
   # 检查系统状态
   python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%')"
   
   # 调整进程数(如果需要)
   # 修改 src/utils/ocr_optimizer.py 中的参数
   ```

3. **内存不足**
   ```bash
   # 检查内存使用
   python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"
   
   # 减少批量处理大小
   # 修改 batch_size 参数
   ```

### 监控命令

```bash
# 实时监控CPU
watch -n 1 "python -c \"import psutil; print(f'CPU: {psutil.cpu_percent()}%')\""

# 查看OCR进程
ps aux | grep -E "(ocr|tesseract)"

# 检查系统负载
top -o cpu
```

## 📈 性能基准

### 测试环境
- **CPU**: Apple M4 Max (14核)
- **内存**: 36GB
- **测试文档**: 100页扫描版PDF

### 性能对比

| 版本 | CPU峰值 | 平均CPU | 处理速度 | 系统稳定性 |
|------|---------|---------|----------|------------|
| v1.0 | 100% | 95% | 3页/秒 | ❌ 易死机 |
| v2.0 | 85% | 65% | 1.5页/秒 | ✅ 稳定 |

### 优化效果

- **CPU保护**: 100% → 85% (降低15%)
- **系统稳定性**: 显著提升
- **处理速度**: 适度降低但更稳定
- **用户体验**: 系统响应流畅

## 🔄 更新日志

### v2.0.1 (2025-12-11)
- ✅ 新增紧急停止机制
- ✅ 降低CPU保护阈值 (95% → 85%)
- ✅ 限制最大进程数 (8 → 4)
- ✅ 缩短超时时间 (20分钟 → 10分钟)
- ✅ 修复临时文件清理问题
- ✅ 增强实时监控 (1秒 → 0.5秒)

### v2.0.0 (2025-12-10)
- ✅ 初始CPU保护机制
- ✅ 动态进程数调整
- ✅ 实时CPU监控
- ✅ 自动暂停机制

## 💡 最佳实践

### 使用建议

1. **分批处理**: 大量文档分批上传，避免一次性处理
2. **监控CPU**: 定期检查CPU使用率
3. **合理配置**: 根据系统性能调整参数
4. **及时清理**: 定期清理临时文件

### 配置优化

```python
# 低性能设备配置
max_workers = 2
cpu_threshold = 70
batch_size = 10

# 高性能设备配置  
max_workers = 4
cpu_threshold = 85
batch_size = 30
```

## 🔗 相关文件

- `src/utils/ocr_optimizer.py` - OCR优化器
- `src/utils/batch_ocr_processor.py` - 批量处理器
- `emergency_cpu_stop.py` - 紧急停止脚本
- `ocr_worker.py` - OCR工作进程

## 📞 技术支持

如遇问题，请检查：
1. CPU使用率是否正常
2. 内存是否充足
3. OCR进程是否正常
4. 临时文件是否清理

紧急情况下运行: `python emergency_cpu_stop.py`
