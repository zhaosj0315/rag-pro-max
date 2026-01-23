# RAG Pro Max - Enterprise Intelligent Document Q&A and Data Analysis System

**Current Version**: v9.1.0 (Flagship Evolution)  
![Version](https://img.shields.io/badge/version-v9.1.0-purple)

RAG Pro Max v9.1.0 delivers an **"Ultra-Performance"** leap. By deeply integrating Component-Level Fragment Isolation, the system achieves a **"Zero White Screen"** interaction experience, setting a new industry standard for responsiveness and chat continuity.

---

## 🚀 v9.1.0 Key Features

### ⚡ Ultra-Performance: Zero White Screen UX
- **Fragment-Based Isolation**: Deeply integrated `st.fragment` technology. Toggling features, adjusting parameters, and configuring data sources now happen with **0ms full-page flashes**.
- **Seamless Chat Flow**: Completely refactored the core scheduler to remove redundant reruns. The entire process from "Input" to "Streaming Response" to "Follow-up Suggestions" is now one contiguous, uninterrupted flow.
- **Latency Near Zero**: Perception latency from query submission to the first character appearing has been reduced by over 90%.

### 💬 Decoupled Pure Chat
- **Zero FS Dependency**: Pure Chat mode is now fully decoupled from the Knowledge Base filesystem. No physical indexing or directory structures are required.
- **Direct LLM Streaming**: Implemented a robust direct-to-LLM streaming channel that automatically handles both raw generators and wrapped response objects (Ollama/OpenAI compatible).

### 📥 Omni-Ingestion (AND Logic)
- **Multi-Source Aggregation**: Build knowledge bases by simultaneously uploading files, adding local paths, and pasting text.
- **Physical Staging Area**: Integrated `task_staging_dir` mechanism with real-time file counting and manual clearing.

### 🔌 Heterogeneous DB Integration (9+ Protocols)
- **Extreme Adaptability**: Native support for MySQL, PostgreSQL, SQLite, DuckDB, ClickHouse, SQL Server, Oracle, MaxCompute, and Snowflake.
- **4D Data Peek**: Explore schema definitions, sample data, relationship graphs, and business insights directly from the sidebar.

---

## 🛠️ Installation & Launch

1. **Prerequisites**: Python 3.10+ / macOS (Recommended) or Linux
2. **Install Dependencies**: `pip install -r requirements.txt`
3. **Start System**: `streamlit run src/apppro.py`

---

**🎯 Goal**: To provide enterprise users with the most professional, ultra-fluid, and stable Smart Dual-Core Analysis and RAG solution!