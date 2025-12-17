# OCR 日志记录系统

## 1. 系统概述

OCR 日志记录系统用于跟踪和分析 OCR (光学字符识别) 处理的性能、成功率和资源消耗。该系统自动记录每次 OCR 操作的详细信息，并提供统计分析功能。

## 2. 日志结构

### 2.1 日志文件位置
所有 OCR 日志存储在 `app_logs/` 目录下，命名格式为 `ocr_stats_YYYYMMDD.json`。

### 2.2 数据格式 (JSON)
```json
{
  "timestamp": "2025-12-17 10:30:45",
  "file_name": "document.pdf",
  "page_count": 5,
  "processing_time": 12.5,
  "status": "success",
  "ocr_engine": "PaddleOCR",
  "device": "GPU",
  "cpu_usage_avg": 45.2,
  "memory_usage_peak": 1024.5
}
```

## 3. 功能特性

- **自动记录**: 每次 OCR 处理自动触发记录。
- **性能统计**: 记录每页平均耗时、总耗时。
- **资源监控**: 记录处理期间的 CPU 和内存使用情况。
- **错误追踪**: 记录失败原因和堆栈信息。

## 4. 使用方法

### 4.1 查看统计
在 "🔧 工具" -> "系统工具" 面板中，或使用命令行工具 `view_ocr_logs.py` (如果有)。

### 4.2 配置
在 `config/app_config.json` 中可配置日志保留天数和详细程度。

## 5. 故障排除

如果发现 OCR 性能下降，请检查日志中的 `processing_time` 和 `device` 字段，确认是否正确使用了 GPU 加速。
