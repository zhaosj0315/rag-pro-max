# RAG Pro Max - Enterprise AI Document QA & Data Analysis System

**Current Version**: v8.8.0 (Flagship Unified Edition)  
![Version](https://img.shields.io/badge/version-v8.8.0-purple)

RAG Pro Max v8.8.0 represents the ultimate evolution of **"Minimalist Unified Architecture"**. By consolidating data ingestion into three all-encompassing entry points and integrating with 9+ heterogeneous databases, the system serves as an enterprise-grade data hub, capable of ingesting and analyzing global data in one stop.

---

## 🚀 v8.8.0 Core Features

### 🔌 Omni-Source Database Integration (9+ DB Support)
- **Wide Adaptation**: Native support for MySQL, PostgreSQL, SQLite, DuckDB, ClickHouse, SQL Server, Oracle, MaxCompute (DataWorks), Snowflake.
- **4D Panoramic View**: Provides field definitions, 50-row sampling, physical foreign key associations, and business insights statistics in the admin panel.

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