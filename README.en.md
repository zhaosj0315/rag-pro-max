# RAG Pro Max - Enterprise Intelligent Document Q&A and Data Analysis System

**Current Version**: v9.5.1 (Omni-Source Unification)  
![Version](https://img.shields.io/badge/version-v9.5.1-purple)

RAG Pro Max v9.5.1 delivers a milestone update in **"Omni-Architecture Unification"**. By adopting the "Everything is a Source File" philosophy, we have unified Database Snapshots, Web Crawling, and Local Files into a single, seamless pipeline.

---

## 🚀 v9.5.1 Key Features

### ⚡ Ultra-Performance: Zero White Screen UX
- **Fragment-Based Isolation**: Deeply integrated `st.fragment` technology. Toggling features, adjusting parameters, and configuring data sources now happen with **0ms full-page flashes**.
- **Seamless Chat Flow**: Completely refactored the core scheduler to remove redundant reruns. The entire process from "Input" to "Streaming Response" to "Follow-up Suggestions" is now one contiguous, uninterrupted flow.
- **Latency Near Zero**: Perception latency from query submission to the first character appearing has been reduced by over 90%.

### 📥 Omni-Ingestion Center (The Unified 5)
- **Unified Entry Point**: A single "Omni-Ingestion" panel replaces scattered upload methods.
- **5-Dimensional Sources**: Supports **Files, Directories, Text Paste, Web Crawling, and Database Snapshots**.
- **Database Snapshots**: Native support for exporting tables or custom SQL queries from 9+ databases (MySQL, Oracle, etc.) directly into the staging area as standard CSV files.
- **Physical Staging**: All data, regardless of source, is materialized into `task_staging_dir` for unified processing.

### 💬 Decoupled Pure Chat
- **Zero FS Dependency**: Pure Chat mode is now fully decoupled from the Knowledge Base filesystem. No physical indexing or directory structures are required.
- **Direct LLM Streaming**: Implemented a robust direct-to-LLM streaming channel that automatically handles both raw generators and wrapped response objects (Ollama/OpenAI compatible).

### 🕷️ Exponential Crawler
- **5+25 Expansion**: Strictly adheres to the $n^1 + n^2$ distribution model. Inputting 2x5 yields 30+ deeply related documents.
- **Logic Unification**: Synchronous, Asynchronous, and Concurrent crawlers now share 100% identical behavior logic.

---

## 🛠️ Installation & Launch

1. **Prerequisites**: Python 3.10+ / macOS (Recommended) or Linux
2. **Install Dependencies**: `pip install -r requirements.txt`
3. **Start System**: `streamlit run src/apppro.py`

---

**🎯 Goal**: To provide enterprise users with the most professional, ultra-fluid, and stable Smart Dual-Core Analysis and RAG solution!