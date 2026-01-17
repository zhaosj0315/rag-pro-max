# RAG Pro Max

<div align="center">

**Languages:** 
[🇨🇳 中文](README.md) | 
[🇺🇸 English](README.en.md)

</div>

---

# RAG Pro Max - Enterprise AI Document QA & Data Analysis System

**Version**: v6.7.0 (Governance & Attachment Unification)  
![Version](https://img.shields.io/badge/version-v6.7.0-brightgreen)

RAG Pro Max is an enterprise-grade agent system that integrates full-scale document migration (RAG), automated web crawling, and physical-loop data analysis.

---

## 🚀 v6.7.0 Key Features

### 🛡️ Unified Governance Matrix
- **Physical Perspective**: Real-time filesystem scanning shows "Creation Date" and "Last Modified" for knowledge bases, increasing governance efficiency by 200%.
- **Deterministic Batch Operations**: Fixes state loss in tables, supporting "Select All" for bulk physical deletion or permission transfers.

### 📎 Universal Attachment Parsing
- **Pipeline Unification**: Chat attachments now share 100% of the same underlying parsing kernel as KB construction, supporting 20+ formats (CSV/Excel/Code).
- **Multi-image OCR Append**: Perfect for multi-turn image QA, automatically merging recognized content.

### 🧠 Data Analyst 2.0 (Build-First Architecture)
- **Build-Phase Physical Loop**: Follows the "Build-First" principle. All tasks from Schema extraction to physical DB (SQLite) injection are completed during the build phase.
- **Synthetic Bootstrapping**: Automatically generates simulation data for logical documents, ensuring meaningful responses from the very first question.
- **Drill-Down Analysis**: Supports continuous probing based on anomalies found in previous steps, automatically inheriting SQL context.

### 🕷️ Saturation Crawl Engine
- **Saturation Queue**: Replaces BFS recursion with a saturation queue mode to ensure 100% capture of large documentation sites.
- **Anti-Scraping Protection**: Intelligent throttling combined with random physical delays to evade WAF firewalls.

---

## 📚 Documentation Center

### 📂 Core Implementation & Architecture (For Developers)
- [📐 **System Architecture**](ARCHITECTURE.md) - Latest v6.7.0 definition
- [💎 **Core Feature Implementation**](CORE_FEATURE_IMPLEMENTATION.md) - Underlying logic of 5 core features (🆕)
- [📊 **Data Analysis Workflow**](DATA_ANALYSIS_WORKFLOW.md) - Physical loop & simulation standards (🆕)
- [🔧 **API Documentation**](API_DOCUMENTATION.md) - Backend service definitions

### 📖 User Guides
- [📘 **Enterprise User Manual**](USER_MANUAL.md) - Full operation guide
- [🎭 **Mock Data Guide**](docs/MOCK_DATA_GUIDE.md) - Comprehensive simulation guide (🆕)
- [❓ **FAQ**](FAQ.md) - Troubleshooting and solutions
- [🚀 **First Time Guide**](docs/standards/FIRST_TIME_GUIDE.md) - 5-minute deployment

### 🛠️ Standards & Management
- [🧹 **Material Maintenance Guide**](docs/standards/MATERIAL_MAINTENANCE_GUIDE.md)
- [📝 **Documentation Standard**](docs/standards/DOCUMENTATION_MAINTENANCE_STANDARD.md)
- [🔒 **Push Standard**](docs/standards/NON_ESSENTIAL_PUSH_STANDARD.md)

---

## 🏗️ Installation

### Requirements
- **Python**: 3.10+
- **Memory**: 8GB+
- **Disk**: 10GB+ (for model cache)

### Quick Start
```bash
git clone https://github.com/zhaosj0315/rag-pro-max.git
cd rag-pro-max
pip install -r requirements.txt
./start.sh
```

---

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

<div align="center">

Made with ❤️ by RAG Pro Max Team

</div>