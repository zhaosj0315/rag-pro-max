# RAG Pro Max - Enterprise Intelligent Document Q&A and Data Analysis System

**Current Version**: v9.7.0 (Unified Governance & Monitoring Edition)  
![Version](https://img.shields.io/badge/version-v9.7.0-purple)

RAG Pro Max v9.7.0 introduces **"Unified Governance & Monitoring"**. The system completely reconstructs the monitoring and scheduling architecture, migrating them from the frontend to the backend **Resource Governance Center**, achieving strict permission isolation. Combined with the **Panoramic Log System**, it provides a "God Mode" view from user behavior to system kernel.

---

## 🚀 v9.7.0 Key Features

### 🛡️ Governance & Monitoring Fusion
- **Monitoring Reduction**: Completely removed the **"📊 Monitor"** entry from the main sidebar, purifying the frontend.
- **Backend Integration**: Migrated **"Real-time System Monitoring"** and **"Intelligent Scheduling"** to the backend **"Resource Governance"** panel.
- **Strict Isolation**: Only Admin roles can view system load and scheduling policies.
- **Panoramic Log System**: Deeply integrated **"Behavior Audit"** and **"System Terminal Logs"**, adding a strategic dashboard and dual-view switching.

### 🎨 Minimalist Monitoring UI
- **Single-Line Stream**: Reconstructed the monitoring panel header into a **single-line 5-column layout**, consolidating title, countdown, refresh stats, progress, and buttons.
- **Visual Noise Reduction**: Physically removed redundant bottom controls; trend charts now expand by default.

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