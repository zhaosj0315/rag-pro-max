# Stage 5 - 性能优化计划

**版本**: v1.3.0  
**状态**: 📋 规划中  
**预计收益**: 处理速度提升 30-50%

---

## 🎯 优化目标

### 当前性能
- 6 个文件处理时间: ~4 秒
- 主要耗时: 元数据提取 + 摘要队列 + 向量化

### 目标性能
- 6 个文件处理时间: ~2-3 秒
- 提升: 30-50%

---

## 📊 性能分析

### 当前处理流程
```
步骤1: 检查索引 (0.1s)
步骤2: 扫描文件 (0.1s)
步骤3: 读取文档 (0.5s)
步骤4: 构建清单 (0.1s)
步骤5: 解析片段 (1.0s)  ⚠️ 耗时
  - 元数据提取 (0.5s)
  - 摘要队列 (0.3s)
步骤6: 向量化 (2.0s)
总计: ~4s
```

### 瓶颈分析
1. **元数据提取** (0.5s)
   - 对少量文件用单线程
   - 计算文件哈希、关键词、分类
   - 可选化

2. **摘要队列** (0.3s)
   - 同步写入 JSON
   - 文本清理耗时
   - 可异步

3. **向量化** (2.0s)
   - 这是必需的，无法跳过
   - 已经使用 GPU 加速

---

## 🚀 优化方案

### 5.1 元数据提取可选化

**目标**: 让用户选择是否提取元数据

**实现**:
```python
# IndexBuilder 添加参数
def __init__(self, ..., extract_metadata: bool = True):
    self.extract_metadata = extract_metadata

# 在 _parse_documents 中判断
if self.extract_metadata:
    self._extract_metadata(...)
else:
    # 跳过，只保存基本信息
```

**收益**: 
- 跳过元数据: 节省 0.5s (12.5%)
- 适合快速测试场景

---

### 5.2 摘要队列异步化

**目标**: 摘要生成不阻塞主流程

**实现**:
```python
# 使用线程异步写入
import threading

def _queue_summaries_async(self, ...):
    def write_queue():
        # 异步写入 JSON
        with open(queue_file, 'w') as f:
            json.dump(...)
    
    thread = threading.Thread(target=write_queue)
    thread.start()
    # 不等待完成
```

**收益**:
- 节省 0.3s (7.5%)
- 用户体验更流畅

---

### 5.3 批量处理优化

**目标**: 减少重复操作

**实现**:
```python
# 批量读取文件信息
def _build_manifest_batch(self, files):
    # 一次性获取所有文件信息
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(get_file_info, files)
    return list(results)
```

**收益**:
- 节省 0.2s (5%)
- 减少 I/O 次数

---

### 5.4 缓存机制

**目标**: 避免重复计算

**实现**:
```python
# 缓存文件哈希
@lru_cache(maxsize=1000)
def get_file_hash(filepath):
    # 计算哈希
    ...

# 缓存嵌入向量
class EmbeddingCache:
    def get_or_compute(self, text):
        if text in cache:
            return cache[text]
        embedding = model.embed(text)
        cache[text] = embedding
        return embedding
```

**收益**:
- 重复文件: 节省 50%+ 时间
- 适合增量更新

---

## 📈 预期效果

### 优化前
```
6 个文件: 4.0s
100 个文件: 60s
```

### 优化后（全部启用）
```
6 个文件: 2.5s (-37.5%)
100 个文件: 40s (-33%)
```

### 优化后（跳过元数据）
```
6 个文件: 2.0s (-50%)
100 个文件: 30s (-50%)
```

---

## 🎛️ 配置选项

### 用户可选
```python
# 在侧边栏添加性能选项
with st.expander("⚡ 性能选项"):
    extract_metadata = st.checkbox(
        "提取元数据", 
        value=True,
        help="关闭可加快 50% 处理速度，但会丢失文件分类、关键词等信息"
    )
    
    async_summary = st.checkbox(
        "异步生成摘要",
        value=True,
        help="后台生成摘要，不阻塞主流程"
    )
```

---

## 📝 实施步骤

### Phase 1: 元数据可选化 (1小时)
1. IndexBuilder 添加 `extract_metadata` 参数
2. 修改 `_parse_documents` 逻辑
3. 添加 UI 配置选项
4. 测试验证

### Phase 2: 摘要异步化 (30分钟)
1. 修改 `_queue_summaries` 为异步
2. 添加线程安全处理
3. 测试验证

### Phase 3: 批量优化 (1小时)
1. 优化文件信息读取
2. 批量处理文件哈希
3. 性能测试

### Phase 4: 缓存机制 (2小时)
1. 实现文件哈希缓存
2. 实现嵌入向量缓存
3. 缓存失效策略
4. 测试验证

**总计**: 4.5 小时

---

## ⚠️ 注意事项

### 权衡
1. **跳过元数据**: 速度快但丢失信息
2. **异步摘要**: 可能导致摘要延迟生成
3. **缓存**: 占用更多内存

### 建议
- 默认启用所有优化
- 让用户根据需求选择
- 提供"快速模式"和"完整模式"

---

## 🧪 测试计划

### 性能测试
```bash
# 测试不同文件数量
- 6 个文件
- 50 个文件
- 100 个文件

# 测试不同配置
- 全部启用
- 跳过元数据
- 异步摘要
```

### 功能测试
- 确保跳过元数据后功能正常
- 确保异步摘要正确生成
- 确保缓存命中率

---

## 📊 成功指标

- ✅ 6 个文件处理时间 < 3s
- ✅ 100 个文件处理时间 < 45s
- ✅ 用户可选配置
- ✅ 功能完整性不受影响
- ✅ 测试全部通过

---

**是否开始 Stage 5 性能优化？**
