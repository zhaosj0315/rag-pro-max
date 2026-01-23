# RAG Pro Max 核心功能实现详述 (Core Feature Implementation)

**版本**: v9.1.0 (Flagship Evolution)
**状态**: 关键性资产 (永久保存)
**描述**: 本文档记录了 v9.1「极致性能」优化、v9.0「全能摄入」逻辑及 v8.9「精准抓取」架构的底层实现、协同算法及物理闭环规范。

---

## ⚡ 1. 极致 UI 性能优化 (UI Performance Hardening)
v9.1.0 对表现层执行了深度手术，解决了 Streamlit 传统的刷新延迟痛点，实现了“零白屏”交互。

### 技术实现细节 (Technical Specs)
1. **组件级局部刷新 (Fragment Isolation)**:
   - 深度应用 `@st.fragment` 装饰器，将工具栏、功能开关及数据源配置区域包装为独立生命周期单元。
   - 内部状态变更（如切换联网搜索、勾选全选）仅触发局部 DOM 更新，绕过整页重绘流程。
2. **对话流无缝衔接 (Seamless Chat Pipeline)**:
   - **去重载调度**: 彻底移除了核心调度器 (`Core Scheduler`) 中用于状态同步的 `st.rerun()` 调用。
   - **原地增量渲染**: 移除了回答生成结束后的刷新指令。通过手动渲染建议按钮并配合**稳定 Key 映射算法** (`dyn_sug_{msg_hash}`)，实现了输出结束与后续交互的瞬间转换。
3. **变量作用域稳健性**: 实施了全局初始化策略，解决了引入局部刷新后 `btn_start` 等变量在主进程中“失踪”的问题。

---

## 💬 2. 纯对话模式深度解耦 (Pure Chat Decoupling)
剥离了轻量级聊天对重型知识库引擎的硬编码依赖。

- **Filesystem-Agnostic**: 识别 `active_kb_name == 
