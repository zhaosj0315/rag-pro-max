# Bug: 回答内容消失

**严重程度**: 🔴 高  
**发现时间**: 2025-12-09  
**状态**: 待修复

---

## 问题描述

用户提问后，AI 回答的内容消失，只显示统计信息。

**表现**:
```
⏳ 正在检索并思考...
⏱️ 3.4秒 | 📝 约 219 字符
📊 详细统计
🚀 速度: 63.6 tokens/s
```

**缺失**: 实际的回答文本内容

---

## 根本原因

`msg_placeholder.markdown(full_text)` 在 `with st.status()` 块内部。

当 status 块关闭时，其内部的所有内容都会被清除，包括回答文本。

**问题代码** (src/apppro.py:2351-2400):
```python
with st.chat_message("assistant", avatar="🤖"):
    msg_placeholder = st.empty()
    with st.status("⏳ 正在检索并思考...", expanded=True):
        try:
            # ... 检索和生成 ...
            for token in response.response_gen:
                full_text += token
                msg_placeholder.markdown(full_text + "▌")
            
            msg_placeholder.markdown(full_text)  # ❌ 在 status 内部
            
        # 提取统计信息...
        except Exception as e:
            # ...
```

当 `with st.status()` 块结束时，`msg_placeholder` 的内容被清除。

---

## 解决方案

### 方案 A: 在 status 外部再次显示（推荐）

```python
with st.chat_message("assistant", avatar="🤖"):
    msg_placeholder = st.empty()
    with st.status("⏳ 正在检索并思考...", expanded=True):
        try:
            # ... 检索和生成 ...
            for token in response.response_gen:
                full_text += token
                msg_placeholder.markdown(full_text + "▌")
            
            msg_placeholder.markdown(full_text)
    
    # ✅ status 块结束后，再次显示确保不消失
    msg_placeholder.markdown(full_text)
    
    # 继续显示统计信息...
```

### 方案 B: 使用不同的 placeholder

```python
with st.chat_message("assistant", avatar="🤖"):
    status_placeholder = st.empty()
    msg_placeholder = st.empty()
    
    with status_placeholder:
        with st.status("⏳ 正在检索并思考...", expanded=True):
            # ... 检索和生成 ...
            for token in response.response_gen:
                full_text += token
                msg_placeholder.markdown(full_text + "▌")
    
    # status 在独立的 placeholder 中，不影响 msg_placeholder
    msg_placeholder.markdown(full_text)
```

---

## 修复步骤

1. 找到 `src/apppro.py` 第 2395 行附近
2. 在 `with st.status()` 块结束后
3. 在 try 块内部（except 之前）
4. 添加: `msg_placeholder.markdown(full_text)`

**注意**: 必须在 try 块内，因为 `full_text` 变量在 try 块中定义。

---

## 测试验证

修复后测试：
1. 提问任意问题
2. 等待回答生成
3. 确认回答文本显示
4. 确认统计信息也显示

---

## 相关文件

- `src/apppro.py` - 主应用文件
- 行号: ~2351-2560

---

## 优先级

🔴 **高优先级** - 影响核心功能，用户无法看到回答

