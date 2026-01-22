# RAG Pro Max - Enterprise Intelligent Document Q&A and Data Analysis System

**Current Version**: v9.0.0 (Flagship Evolution)  
![Version](https://img.shields.io/badge/version-v9.0.0-purple)

RAG Pro Max v9.0.0 inaugurates the **"Omni-Ingestion"** era. By introducing a physical Staging Area mechanism, the system enables "AND logic" aggregation across files, directories, and pasted text, significantly enhancing information integration efficiency.

---

## 🚀 v9.0.0 Key Features

### 📥 Omni-Ingestion (AND Logic)
- **Multi-Source Aggregation**: No more "OR" choices. Simultaneously upload files, add local paths, and paste text to build a comprehensive knowledge base.
- **Physical Staging Area**: Integrated `task_staging_dir` mechanism with real-time file counting and manual clearing.
- **Admin Quota Exemption**: Administrators enjoy unlimited storage, with fine-grained control to allocate space via the "Individual Security Cabin" UI.

### 🕷️ Crawler Precision Upgrade
- **Seed Isolation**: Seed URLs act as Level 0, freeing up quotas for descendants.
- **Exponential Diffusion**: Strict adherence to $n^1 + n^2$ layer distribution (e.g., 5+25 crawl pattern).

### 🎨 Sidebar Interaction Revolution (Unified Ingestion)
- **Three Core Pillars**: Interface refactored into **📂 File Upload (incl. Paste/Path), 🌐 Internet Extraction (incl. Crawler/Search), 🔌 Database Sync**.
- **Intelligent Intent Recognition**: In Internet Extraction mode, automatically routes to precise crawler or global search engine based on input (URL or Keyword).
- **Universal Attachment Integration**: "📝 Paste Text" and "Local Path" are deeply integrated into the File Upload panel, supporting auto-save on blur.
- **Instant Peek**: Click the **`👁️`** icon when selecting tables to preview data instantly in a sidebar bubble.

### ⚡ Smart Linkage for QA Modes
- **Detect & Activate**: Automatically senses KB capabilities and toggles the "Data Analysis" switch for the user.
- **Unified Naming**: Global KB name component with 💡 smart naming suggestions across all ingestion modes.

### 🕸️ Smart Schema Graph Builder
- **Deep Profiling**: Automatically identifies Primary Keys (PK), Enums, and infers relational join graphs for complex SQL inference.

## 🛠️ Installation & Launch

1. **Prerequisites**: Python 3.10+ / macOS (Recommended) or Linux
2. **Install Dependencies**: `pip install -r requirements.txt`
3. **Start System**: `streamlit run src/apppro.py`

---

**🎯 Goal**: To provide enterprise users with the most professional, high-performance, and stable Smart Dual-Core Analysis and RAG solution!