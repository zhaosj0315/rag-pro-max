# 故障排除指南

## 🚨 CPU相关问题

### CPU使用率过高 (>95%)

**症状**: 系统响应缓慢，风扇高速运转，可能死机

**解决方案**:
```bash
# 1. 立即停止OCR进程
python emergency_cpu_stop.py

# 2. 检查CPU使用率
python -c "import psutil; print(f'CPU: {psutil.cpu_percent()}%')"

# 3. 重启应用
./start.sh
```

**预防措施**:
- 分批处理大量文档
- 监控CPU使用率
- 调整OCR进程数限制

### OCR处理缓慢

**症状**: OCR处理速度明显下降

**诊断**:
```bash
# 检查系统资源
python -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'Available cores: {psutil.cpu_count()}')
"
```

**解决方案**:
1. **CPU过高**: 等待CPU降温或重启系统
2. **内存不足**: 关闭其他应用程序
3. **进程数过多**: 检查OCR优化器配置

### 系统死机/无响应

**紧急处理**:
```bash
# 强制终止Python进程
pkill -f python

# 或者重启系统
sudo reboot
```

**预防配置**:
```python
# 修改 src/utils/ocr_optimizer.py
max_cpu_usage = 80.0  # 降低CPU限制
max_workers = 2       # 减少进程数
```

## 📁 文件处理问题

### 文件上传失败

**常见原因**:
- 文件过大 (>100MB)
- 文件格式不支持
- 磁盘空间不足
- 权限问题

**解决方案**:
```bash
# 检查磁盘空间
df -h

# 检查文件权限
ls -la temp_uploads/

# 清理临时文件
rm -rf temp_uploads/*
```

### OCR识别失败

**症状**: PDF处理后无文本内容

**检查步骤**:
1. **确认是扫描版PDF**: 尝试复制PDF中的文字
2. **检查OCR依赖**: 确保tesseract已安装
3. **查看错误日志**: 检查app_logs/目录

**修复方法**:
```bash
# 重新安装OCR依赖
pip install pytesseract pdf2image

# macOS安装tesseract
brew install tesseract

# 测试OCR功能
python -c "import pytesseract; print('OCR可用')"
```

## 🔍 检索问题

### 查询无结果

**可能原因**:
- 知识库为空
- 嵌入模型未加载
- 查询词不匹配

**诊断步骤**:
```bash
# 检查知识库
ls -la vector_db_storage/

# 检查嵌入模型
python -c "
from src.utils.model_manager import load_embedding_model
model = load_embedding_model('BAAI/bge-small-zh-v1.5', 'HuggingFace')
print('嵌入模型正常' if model else '嵌入模型异常')
"
```

### 查询速度慢

**优化方法**:
1. **调整检索参数**:
   ```json
   // rag_config.json
   {
     "top_k": 3,           // 减少检索数量
     "similarity_threshold": 0.8  // 提高相似度阈值
   }
   ```

2. **清理向量数据库**:
   ```bash
   # 重建索引
   rm -rf vector_db_storage/your_kb_name/
   # 重新上传文档
   ```

## 💾 内存问题

### 内存不足

**症状**: 应用崩溃，OOM错误

**解决方案**:
```bash
# 检查内存使用
python -c "
import psutil
mem = psutil.virtual_memory()
print(f'内存使用: {mem.percent}%')
print(f'可用内存: {mem.available/1024/1024/1024:.1f}GB')
"

# 清理内存
python -c "
import gc
from src.utils.memory import cleanup_memory
cleanup_memory()
print('内存已清理')
"
```

**预防措施**:
- 减少批量处理大小
- 定期重启应用
- 关闭不必要的程序

## 🌐 网络问题

### API连接失败

**症状**: "Connection error" 错误

**检查网络**:
```bash
# 测试网络连接
curl -I https://api.openai.com/v1/models

# 检查代理设置
echo $HTTP_PROXY
echo $HTTPS_PROXY
```

**解决方案**:
1. **使用本地模型**: 配置Ollama
2. **检查API密钥**: 确认密钥有效
3. **网络代理**: 配置正确的代理

### 离线模式问题

**启用离线模式**:
```python
# 在应用中设置
st.session_state.OFFLINE_MODE = True
```

**离线功能**:
- ✅ 文档上传和处理
- ✅ 向量检索
- ❌ AI回答生成 (需要本地LLM)

## 🔧 配置问题

### 模型加载失败

**检查模型**:
```bash
# 检查HuggingFace缓存
ls -la hf_cache/

# 重新下载模型
rm -rf hf_cache/BAAI--bge-small-zh-v1.5/
# 重启应用自动下载
```

### 配置文件错误

**重置配置**:
```bash
# 备份当前配置
cp config/app_config.json config/app_config.json.bak

# 使用默认配置
git checkout config/app_config.json
```

## 📊 性能监控

### 实时监控命令

```bash
# CPU监控
watch -n 1 "python -c \"import psutil; print(f'CPU: {psutil.cpu_percent()}%')\""

# 内存监控
watch -n 1 "python -c \"import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')\""

# 进程监控
watch -n 1 "ps aux | grep -E '(ocr|tesseract|python)' | head -10"

# GPU监控 (如果有)
watch -n 1 "nvidia-smi"
```

### 日志分析

```bash
# 查看最新日志
tail -f app_logs/log_$(date +%Y%m%d).jsonl

# 搜索错误
grep -i error app_logs/log_*.jsonl

# 分析性能
python view_logs.py --stats
```

## 🆘 紧急恢复

### 完全重置

```bash
# 1. 停止所有进程
pkill -f "python.*rag"
pkill -f "streamlit"

# 2. 清理所有数据
rm -rf vector_db_storage/*
rm -rf chat_histories/*
rm -rf temp_uploads/*
rm -rf app_logs/*

# 3. 重置配置
git checkout config/

# 4. 重新启动
./start.sh
```

### 备份恢复

```bash
# 创建备份
tar -czf rag_backup_$(date +%Y%m%d).tar.gz \
  vector_db_storage/ chat_histories/ config/

# 恢复备份
tar -xzf rag_backup_20251211.tar.gz
```

## 📞 获取帮助

### 收集诊断信息

```bash
# 生成诊断报告
python -c "
import sys, psutil, platform
print(f'Python: {sys.version}')
print(f'Platform: {platform.platform()}')
print(f'CPU: {psutil.cpu_count()} cores')
print(f'Memory: {psutil.virtual_memory().total/1024/1024/1024:.1f}GB')
print(f'CPU Usage: {psutil.cpu_percent()}%')
print(f'Memory Usage: {psutil.virtual_memory().percent}%')
"
```

### 常用检查命令

```bash
# 快速健康检查
python tests/factory_test.py

# 检查依赖
pip list | grep -E "(streamlit|llama|torch)"

# 检查文件权限
ls -la src/utils/ocr_optimizer.py
ls -la emergency_cpu_stop.py
```

### 联系支持

如果问题仍然存在，请提供：
1. 错误信息截图
2. 系统诊断信息
3. 操作步骤
4. 日志文件 (app_logs/)

紧急情况下，运行: `python emergency_cpu_stop.py`
