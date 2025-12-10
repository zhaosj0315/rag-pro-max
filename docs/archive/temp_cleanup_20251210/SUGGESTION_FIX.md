# 推荐问题重复修复 - v1.7.3

## 问题描述

用户反馈：点击推荐问题后，系统提示"您刚才已经问过相同的问题"，这是因为推荐系统生成了重复的问题。

## 根本原因

1. **历史记录覆盖**: `suggestions_history` 被新推荐直接覆盖，丢失了之前的推荐历史
2. **去重逻辑不完整**: 多个地方的推荐生成逻辑不一致
3. **显示逻辑混乱**: 同时使用 `suggestions_history` 和 `current_suggestions`

## 修复方案

### 1. 历史记录累积策略

**修改前**:
```python
# 直接覆盖，丢失历史
st.session_state.suggestions_history = new_sugs[:3]
```

**修改后**:
```python
# 累积历史，避免重复
if not hasattr(st.session_state, 'suggestions_history'):
    st.session_state.suggestions_history = []

# 过滤重复后添加
new_suggestions = [s for s in new_sugs if s not in st.session_state.suggestions_history]
st.session_state.suggestions_history.extend(new_suggestions)
st.session_state.current_suggestions = new_suggestions[:3]
```

### 2. 完整的去重逻辑

收集所有历史问题：
- 用户问过的问题 (`messages`)
- 历史推荐问题 (`suggestions_history`)
- 队列中的问题 (`question_queue`)
- 当前显示的推荐 (`current_suggestions`)

### 3. 统一显示逻辑

```python
# 优先显示当前推荐，如果没有则显示历史推荐
display_suggestions = (
    st.session_state.get('current_suggestions', []) or 
    st.session_state.get('suggestions_history', [])
)
```

## 修复文件

1. **src/ui/message_renderer.py**
   - 修复 `_generate_more_suggestions` 方法
   - 更新推荐显示逻辑

2. **src/ui/main_interface.py**
   - 修复 `_generate_suggestions` 方法
   - 修复 `_generate_more_suggestions` 方法
   - 更新推荐显示逻辑

## 测试验证

创建了 `test_suggestion_fix.py` 测试脚本：

```bash
python test_suggestion_fix.py
```

**测试结果**:
- ✅ 基本去重功能正常
- ✅ 多次生成累积效果正常
- ✅ 生成9个不重复问题

## 用户体验改进

### 修复前
- 用户点击推荐问题 → "您刚才已经问过相同的问题"
- 每次生成的推荐可能重复
- 用户体验差，需要手动输入问题

### 修复后
- 每次生成的推荐都是全新的
- 不会出现重复提示
- 用户可以连续点击推荐问题进行深度对话

## 技术细节

### 状态管理优化

```python
# 新增状态变量
st.session_state.suggestions_history    # 所有历史推荐（累积）
st.session_state.current_suggestions    # 当前显示的推荐（最新3个）
```

### 去重算法

使用 `_is_similar_question` 函数进行智能去重：
- 完全相同检测
- 包含关系检测  
- 关键词重叠度检测（阈值 0.7）

## 版本信息

- **修复版本**: v1.7.3
- **修复日期**: 2025-12-10
- **影响范围**: 推荐问题生成和显示
- **向后兼容**: ✅ 完全兼容

## 后续优化

1. **智能推荐**: 基于用户兴趣生成更相关的问题
2. **推荐排序**: 根据知识库内容质量排序推荐
3. **个性化**: 基于用户历史偏好调整推荐策略
