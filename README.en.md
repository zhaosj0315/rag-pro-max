# RAG Pro Max - Enterprise Intelligent Document Q&A and Data Analysis System

**Current Version**: v9.8.0 (DA-ECP V4.5 Edition)  
![Version](https://img.shields.io/badge/version-v9.8.0-purple)

RAG Pro Max v9.8.0 introduces the **"DA-ECP V4.5 (Data Analysis Enhanced Construction Protocol)"**. We have shifted the core logic of data understanding from "Query Time" to "Build Time". Through **Micro-Profiling** and **Structure Parsing**, the system achieves deep semantic understanding of business data right at the inception of the Knowledge Base, truly realizing "Construction as Understanding".

---

## 🚀 v9.8.0 Key Features

### 🧠 DA-ECP V4.5 Protocol (Enhanced Construction)
- **Construction as Understanding**: During the build phase, the system not only processes text but actively parses the **"Business Blueprint"** of structured data. Through `StructureParser`, it understands data dictionary files (Excel/CSV) and converts them into logical table structures.
- **Static-Dynamic Separation**: Established the golden rule of **"Solidify Logic at Build, Generate Data at Query"**. The build phase focuses on parsing and semantic modeling, strictly avoiding redundant data generation; the query phase performs precise **JIT (Just-In-Time)** data simulation based on the solidified blueprint.
- **Micro-Profiling**: For solid data tables, the system automatically extracts statistical features (enum distributions, numeric ranges, null rates) to provide rich context for the SQL decision engine.
- **Holographic Terminal Logs**: Reconstructed terminal feedback during the build process, using "Icons + Color Tags" to visualize file arbitration results and semantic modeling progress in real-time.

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