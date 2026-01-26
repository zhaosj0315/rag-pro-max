# RAG Pro Max - Enterprise Intelligent Document Q&A and Data Analysis System

**Current Version**: v9.5.37-stable (Search Revolution Edition)  
![Version](https://img.shields.io/badge/version-v9.5.37-purple)

RAG Pro Max v9.5.37 introduces the **"Search Revolution"**. With Violent Link Discovery and Automatic Redirect Unwrapping, the system ensures 100% web crawling success rates, paired with a full-featured Staging Area Inspector for a professional data orchestration experience.

---

## 🚀 v9.5.37 Key Features

### 🕷️ Smart Search Revolution
- **Violent Discovery Engine**: Uses regex-based raw HTML scanning to bypass module caching and WAF obfuscation.
- **Direct Unwrapping**: Automatically strips redirect wrappers from Bing/DuckDuckGo links for instant document access.
- **Level 0 Seed Logic**: Search engines act as pure "launchpads," ensuring Level 1+ contains only high-value documents.

### 📦 Staging Area Inspector
- **4-in-1 Toolchain**: Integrated **View(📂), Reveal(📍), Refresh(🔄), and Clear(🧹)** for precision control.
- **Audit Reports**: Automatic grouping by source with second-level capture time tracking.
- **Path Self-Healing**: Guaranteed directory persistence during long-running tasks.

### 📥 Omni-Ingestion Center (The Unified 5)
- **Unified Entry Point**: A single "Omni-Ingestion" panel replaces scattered upload methods.
- **5-Dimensional Sources**: Supports **Files, Directories, Text Paste, Web Crawling, and Database Snapshots**.
- **Physical Staging**: All data, regardless of source, is materialized into `task_staging_dir` for unified processing.

### 💬 Decoupled Pure Chat
- **Zero FS Dependency**: Pure Chat mode is now fully decoupled from the Knowledge Base filesystem. No physical indexing or directory structures are required.
- **Direct LLM Streaming**: Implemented a robust direct-to-LLM streaming channel that automatically handles both raw generators and wrapped response objects (Ollama/OpenAI compatible).

---

## 🛠️ Installation & Launch

1. **Prerequisites**: Python 3.10+ / macOS (Recommended) or Linux
2. **Install Dependencies**: `pip install -r requirements.txt`
3. **Start System**: `streamlit run src/apppro.py`

---

**🎯 Goal**: To provide enterprise users with the most professional, ultra-fluid, and stable Smart Dual-Core Analysis and RAG solution!