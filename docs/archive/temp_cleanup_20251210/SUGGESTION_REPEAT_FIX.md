# 推荐问题重复修复 - v1.7.3

## 🎯 问题描述

用户反馈：推荐问题总是重复生成相同的3个问题：
```
1. 这本书的核心观点是什么？
2. 作者的写作背景如何？
3. 有哪些实用的阅读技巧？
```

## 🔍 根本原因

推荐问题生成使用了**降级策略(fallback)**而不是真正的LLM生成：

1. **LLM未正确传递**: `Settings.llm` 在推荐问题生成时未设置
2. **降级策略触发**: 检测到"读书"、"阅读"等关键词，返回固定问题
3. **参数传递缺失**: 调用时没有传递LLM模型参数

## 🛠️ 修复方案

### 1. 增强LLM获取逻辑

**修改前**:
```python
if not hasattr(Settings, 'llm') or not Settings.llm: 
    result["questions"] = get_smart_fallback(context_text)
    return
```

**修改后**:
```python
# 尝试从多个来源获取LLM
llm = None

# 1. 优先使用传入的LLM
if llm_model:
    llm = llm_model

# 2. 从Settings获取
elif hasattr(Settings, 'llm') and Settings.llm:
    llm = Settings.llm

# 3. 从chat_engine获取
elif query_engine and hasattr(query_engine, '_llm'):
    llm = query_engine._llm

if not llm:
    # 使用降级策略
    result["questions"] = get_smart_fallback(context_text)
    return
```

### 2. 添加LLM参数传递

**函数签名修改**:
```python
def generate_follow_up_questions_safe(
    context_text, 
    num_questions=3, 
    existing_questions=None, 
    timeout=10, 
    logger=None, 
    query_engine=None, 
    llm_model=None  # 新增LLM参数
):
```

**调用修改**:
```python
# 获取LLM模型
llm_model = None
if chat_engine and hasattr(chat_engine, '_llm'):
    llm_model = chat_engine._llm

new_sugs = generate_follow_up_questions(
    context_text=msg['content'], 
    num_questions=3,
    existing_questions=all_history_questions,
    query_engine=chat_engine,
    llm_model=llm_model  # 传递LLM
)
```

## 📁 修改文件

1. **src/chat_utils_improved.py**
   - 修改 `generate_follow_up_questions_safe` 函数签名
   - 增强LLM获取逻辑
   - 优先使用传入的LLM参数

2. **src/query/query_processor.py**
   - 修改推荐问题生成调用
   - 从chat_engine提取LLM并传递

3. **src/apppro.py**
   - 修改推荐问题生成调用
   - 添加LLM参数传递

## 🧪 测试验证

### 测试脚本
```bash
python test_llm_fix.py
```

**测试结果**:
```
✅ 生成了真正的推荐问题，LLM工作正常
✨ 生成的推荐问题: [
    '樊登读书会的界面设计有哪些具体特点？', 
    '如何提升用户界面的易用性？', 
    '樊登读书会如何收集用户界面反馈？'
]
```

## 📋 期望效果

### 修复前
```
ℹ️ [16:42:11]    1. 这本书的核心观点是什么？
ℹ️ [16:42:11]    2. 作者的写作背景如何？
ℹ️ [16:42:11]    3. 有哪些实用的阅读技巧？

ℹ️ [16:43:19]    1. 这本书的核心观点是什么？  (重复)
ℹ️ [16:43:19]    2. 作者的写作背景如何？     (重复)
ℹ️ [16:43:19]    3. 有哪些实用的阅读技巧？   (重复)
```

### 修复后
```
ℹ️ [16:45:11]    1. 樊登读书会的界面设计有哪些具体特点？
ℹ️ [16:45:11]    2. 如何通过界面设计提升用户留存率？
ℹ️ [16:45:11]    3. 界面设计对用户学习效果有何影响？

ℹ️ [16:46:19]    1. 樊登读书会如何收集用户反馈？
ℹ️ [16:46:19]    2. 用户界面优化的具体方法有哪些？
ℹ️ [16:46:19]    3. 界面设计如何平衡功能性和美观性？
```

## 🚀 应用修复

### 重启应用
```bash
./restart_app.sh
```

### 验证修复
1. 提问并获得回答
2. 查看推荐问题是否基于上下文生成
3. 点击"继续推荐"查看是否生成新问题
4. 检查日志确认使用LLM而非fallback

## 🎯 技术细节

### LLM获取优先级
1. **传入参数** - `llm_model` 参数
2. **全局设置** - `Settings.llm`
3. **查询引擎** - `query_engine._llm`
4. **降级策略** - 固定问题模板

### 降级策略触发条件
- 所有LLM获取方式都失败
- 记录警告日志
- 使用基于关键词的固定问题

## 🔧 故障排除

### 如果仍然生成重复问题
1. 检查LLM是否正确传递
2. 查看日志中的警告信息
3. 验证chat_engine是否包含LLM
4. 确认应用已重启

### 调试方法
```python
# 在推荐生成前添加调试信息
print(f"LLM available: {llm_model is not None}")
print(f"Chat engine: {chat_engine}")
print(f"Settings.llm: {getattr(Settings, 'llm', None)}")
```
