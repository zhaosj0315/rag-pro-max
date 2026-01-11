# RAG Pro Max v5.3.3 企业级系统架构文档

**版本**: v5.3.3 (Universal Modeling Edition)  
**更新日期**: 2026-01-11  
**适用范围**: 企业级全格式建模、战略推演与高性能 RAG 平台  
**核心特性**: 全域开模分析、虚拟战略沙盒、强制查询路由、零崩溃环境

---

## 🏗️ 整体架构图

### 1. 表现层 (Presentation Layer - Fluid UI)
- **Fluid Layout Engine**: 全宽流式布局，动态渲染“对话流”与“成果流 (Artifacts)”。
- **Strategic Workshop UI**: 专为数据推演设计，支持 Before (采样) -> Logic (SQL) -> After (结论) 的链式剧场展示。

### 2. 服务层 (Service Layer)
- **Data Analyst Engine 15.0 (Strategic Brain)**: 
    - **全域开模 (Universal Modeling)**: 同时处理物理表 (CSV/Excel) 与语义字典 (PDF/MD)，产出统一的业务元模型。
    - **虚拟沙盒 (Strategic Sandbox)**: 针对缺失物理数据的虚拟表，自动生成逻辑闭环的 Mock 数据。
    - **查询路由守卫 (Routing Guard)**: 物理隔离 SQL 分析与 RAG 检索链路，防止输出冲突。
- **RAG Engine**: 支持跨库检索、混合流式协议及自动摘要。

### 3. 系统初始化层 (Lifecycle Layer)
- **Zero-Crash Loader**: 优化了变量初始化顺序（logger -> env -> sys），彻底消除极端并发下的 NameError。

---

## 🧩 核心流程演进 (v5.3.3)

### 1. 全域开模流程 (Universal Modeling)
```
多源输入 (PDF/MD/CSV/SQL)
    ↓
多模态特征蒸馏 (LLM + RAG)
    ↓
统一 Schema 合成 (Unified Business Model)
    ↓
缺失物理表检测
    ↓
虚拟沙盒激活 (Mock Data Injection)
    ↓
SQL 推演与执行
```

---

## 🔧 技术栈 (v5.3.3 对齐)

- **核心大脑**: DataAnalystEngine (v5.3 实现全域开模)
- **仿真引擎**: StrategicMockEngine (基于 LLM 生成 SQL 仿真脚本)
- **前端**: Streamlit (Fragment + Fluid Mode)
- **数据库**: SQLite (含 Dual 物理垫片) + ChromaDB
- **并发控制**: ThreadPoolExecutor (macOS 深度优化)

---

## 🛡️ 安全与审计架构

- **数据完整性**: 内置对账逻辑（Verify Stage），确保仿真数据与逻辑口径的一致性。
- **路由隔离**: 采用强制跳转机制 (st.rerun)，确保分析报告的纯净度。

