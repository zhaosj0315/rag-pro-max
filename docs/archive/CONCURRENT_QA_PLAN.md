# 并发问答优化计划

## 📋 现状分析

### 当前机制（串行排队）
```python
# 检查是否正在处理
if st.session_state.get('is_processing'):
    st.info("⏳ 正在处理上一个问题，新问题已排队...")

# 处理问题
st.session_state.is_processing = True
# ... 处理逻辑 ...
st.session_state.is_processing = False
```

**问题**:
- ❌ 串行处理，用户连续提问需要等待
- ❌ 只能排队1个问题（`prompt_trigger`）
- ❌ 无法并发处理多个问题
- ❌ 用户体验差

---

## 🎯 优化目标

### 方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **方案1: 多线程并发** | 简单，共享内存 | GIL限制，CPU密集型无效 | ⭐⭐ |
| **方案2: 多进程并发** | 真并行，充分利用多核 | 内存开销大，状态同步复杂 | ⭐ |
| **方案3: 异步队列** | 资源可控，顺序保证 | 仍是串行，只是异步 | ⭐⭐⭐ |
| **方案4: 会话隔离** | 完全独立，无冲突 | 需要重构架构 | ⭐⭐⭐⭐ |

---

## 🚀 推荐方案：异步队列 + 会话隔离

### 核心思路
1. **异步队列**: 使用 `ThreadPoolExecutor` 处理问答
2. **会话隔离**: 每个问题独立的 chat_engine 实例
3. **流式显示**: 实时显示多个问题的回答进度
4. **智能限流**: 最多同时处理 2-3 个问题

### 架构设计

```python
class ConcurrentQAManager:
    """并发问答管理器"""
    
    def __init__(self, max_workers=2):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_tasks = {}  # {task_id: Future}
        self.results = {}       # {task_id: result}
    
    def submit_question(self, question, chat_engine, kb_name):
        """提交问题到队列"""
        task_id = f"qa_{int(time.time() * 1000)}"
        
        future = self.executor.submit(
            self._process_question,
            question, chat_engine, kb_name
        )
        
        self.active_tasks[task_id] = future
        return task_id
    
    def _process_question(self, question, chat_engine, kb_name):
        """处理单个问题（在后台线程）"""
        try:
            response = chat_engine.stream_chat(question)
            # 收集完整回答
            full_text = ""
            for token in response.response_gen:
                full_text += token
            
            return {
                "success": True,
                "answer": full_text,
                "sources": response.source_nodes
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_result(self, task_id):
        """获取任务结果（非阻塞）"""
        if task_id not in self.active_tasks:
            return None
        
        future = self.active_tasks[task_id]
        if future.done():
            result = future.result()
            self.results[task_id] = result
            del self.active_tasks[task_id]
            return result
        
        return None  # 仍在处理中
    
    def get_active_count(self):
        """获取活跃任务数"""
        return len(self.active_tasks)
```

### UI 显示

```python
# 初始化管理器
if "qa_manager" not in st.session_state:
    st.session_state.qa_manager = ConcurrentQAManager(max_workers=2)

# 显示活跃任务
active_count = st.session_state.qa_manager.get_active_count()
if active_count > 0:
    st.info(f"⏳ 正在处理 {active_count} 个问题...")

# 提交新问题
if user_input:
    if active_count >= 3:
        st.warning("⚠️ 当前有太多问题在处理，请稍后再试")
    else:
        task_id = st.session_state.qa_manager.submit_question(
            user_input, 
            st.session_state.chat_engine,
            active_kb_name
        )
        st.session_state.pending_tasks.append(task_id)
        st.rerun()

# 检查并显示结果
for task_id in st.session_state.pending_tasks[:]:
    result = st.session_state.qa_manager.get_result(task_id)
    if result:
        # 显示结果
        if result["success"]:
            st.success(f"✅ 回答完成")
            st.markdown(result["answer"])
        else:
            st.error(f"❌ 处理失败: {result['error']}")
        
        st.session_state.pending_tasks.remove(task_id)
        st.rerun()
```

---

## ⚠️ 技术挑战

### 1. Streamlit 限制
**问题**: Streamlit 是单线程框架，不支持真正的并发 UI 更新

**解决方案**:
- 使用 `st.rerun()` 定期刷新
- 后台线程只处理计算，不更新 UI
- 主线程轮询结果并更新 UI

### 2. 资源竞争
**问题**: 多个问题同时查询向量数据库可能冲突

**解决方案**:
- 限制并发数（max_workers=2）
- 使用线程锁保护关键资源
- 每个任务独立的 chat_engine 实例

### 3. 内存占用
**问题**: 多个 chat_engine 实例占用大量内存

**解决方案**:
- 共享 embedding 模型
- 及时清理完成的任务
- 限制最大并发数

---

## 📊 预期效果

### 性能提升
- **连续提问**: 无需等待，立即提交
- **并发处理**: 2-3个问题同时处理
- **响应时间**: 感知延迟降低 50-70%

### 用户体验
- ✅ 连续提问不阻塞
- ✅ 实时显示处理进度
- ✅ 多个问题并行回答
- ✅ 智能限流避免过载

---

## 🔧 实施计划

### Phase 1: 基础框架（2小时）
1. 创建 `ConcurrentQAManager` 类
2. 实现任务提交和结果获取
3. 基础测试

### Phase 2: UI 集成（2小时）
1. 修改主文件问答流程
2. 添加任务状态显示
3. 实现结果轮询和显示

### Phase 3: 资源管理（1小时）
1. 添加并发限制
2. 实现资源清理
3. 错误处理

### Phase 4: 优化和测试（1小时）
1. 性能测试
2. 边界情况测试
3. 文档更新

**总计**: 6小时

---

## 💡 简化方案（推荐先实施）

如果完整方案太复杂，可以先实施简化版：

### 简化版：队列缓冲
```python
# 初始化问题队列
if "question_queue" not in st.session_state:
    st.session_state.question_queue = []

# 提交问题到队列
if user_input:
    st.session_state.question_queue.append(user_input)
    st.info(f"✅ 问题已加入队列（当前 {len(st.session_state.question_queue)} 个）")

# 处理队列中的问题
if not st.session_state.is_processing and st.session_state.question_queue:
    current_question = st.session_state.question_queue.pop(0)
    # 处理 current_question...
```

**优点**:
- 实现简单（30分钟）
- 不改变现有架构
- 支持多个问题排队

**缺点**:
- 仍是串行处理
- 无法并发

---

## 🎯 建议

### 立即实施：简化版队列缓冲
- **时间**: 30分钟
- **效果**: 支持多问题排队，改善用户体验
- **风险**: 低

### 后续实施：完整并发方案
- **时间**: 6小时
- **效果**: 真正并发处理，性能提升 50-70%
- **风险**: 中（需要充分测试）

---

*计划创建时间: 2025-12-09*
*预计完成时间: 30分钟（简化版）/ 6小时（完整版）*
