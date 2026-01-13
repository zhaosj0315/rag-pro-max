# RAG Pro Max

<div align="center">

**Languages:** 
[🇨🇳 中文](README.md) | 
[🇺🇸 English](README.en.md)

</div>

---

# RAG Pro Max - Intelligent Document Q&A System

**Version**: v5.5.8  
![Version](https://img.shields.io/badge/version-v5.5.8-brightgreen)
![Status](https://img.shields.io/badge/status-Stable-blue)
![Last Update](https://img.shields.io/badge/last%20update-2026--01--12-orange)

## 🚀 RAG Pro Max v5.5.8
### 📦 Data Sovereignty & Full Export (v5.5.8 Update)
- **Ultimate Asset Package**: One-click export of 01-06 structure, including raw documents, chat history (MD), strategic models, and vector snapshots.
- **Cross-Directory Salvage**: Automated retrieval of search results from temporary folders to ensure complete data portability.
- **Admin Asset Inventory**: New 'Asset Hub' in admin dashboard for cross-user batch filtering and deep cleanup.
- **Self-Healing Infrastructure**: Optimized log system with automated fallback to user home directory, bypassing macOS permission issues.

## 🚀 RAG Pro Max v5.5.8
### 💎 Universal Strategic Modeling (v5.5.8 Major Update)
- **Multi-modal Alignment**: Supports mixed input of PDF/MD dictionaries and CSV/Excel tables, automatically locking business definitions to physical table structures.
- **Virtual Strategic Sandbox**: Introducing the "Golden Mock Data" engine, enabling one-click simulation of 20 closed-loop data records even with only data dictionaries.
- **Forced Routing Guard**: Completely isolates Data Analysis and RAG pipelines, ensuring professional analysis dashboard outputs via `st.rerun()`.
- **Zero-Crash Stability**: Deeply optimized initialization scopes, eliminating `NameError` for critical variables like `logger` and `time` under extreme loads.
- **Auto-Format Sensing**: System automatically triggers the "Business Semantic Brain" whenever tables or dictionary files are detected.

---

## ✨ Core Features

### 🔒 **Privacy-First & Offline Deployment**
- **Complete Offline Deployment**: Data never leaves your internal network
- **Local Processing**: All computations performed on local servers
- **Zero Data Upload**: 100% local storage of document content
- **Private Customization**: Supports independent operation in intranet environments

### 🏢 **Enterprise-Grade Features**
- **Local LLM Support**: Ollama integration, no internet required
- **Docker Containerization**: Secure environment isolation
- **Self-hosted Vector Database**: Sensitive information stays internal
- **Open Source Transparency**: Complete source code for security auditing

### 🔬 Intelligent Research & Deep Analysis (Enhanced in v5.5.8)
- **Deep Research Mode**: Simulates expert-level multi-step analysis, fact-checking, and cross-domain knowledge integration
- **Research Instruction Injection**: Automatically decomposes complex questions into multi-dimensional analysis
- **Status Indicator Bar**: Real-time display of four core capabilities: "Thinking, Networking, Searching, Researching"

### 🌐 Internet Search & Real-time Enhancement
- **DuckDuckGo Integration**: Automatically fetches latest internet information as real-time supplement to knowledge base
- **Quality Assessment System**: Integrated intelligent quality analyzer with automatic authority scoring (🏆/⭐/⚠️)
- **Collapsible Display**: Search details sorted by quality and collapsed in status bar by default

### 🔄 Continuous Optimization System (New in v5.5.8)
- **Virtuous Cycle Mechanism**: Automated optimization workflow of patrol → analyze → plan → implement → verify
- **Intelligent Monitoring**: Automatic monitoring of code quality, performance metrics, test coverage, documentation completeness
- **Auto Optimization**: Executes automated improvement tasks like cleanup, refactoring, performance tuning
- **Visual Dashboard**: Real-time display of optimization effects and system health status

---

## 🏗️ System Architecture

### Four-Layer Architecture Design
```
Presentation Layer (UI)    - Streamlit Interface Components
    ↓
Service Layer             - Business Logic Services
    ↓  
Common Layer              - Shared Utility Modules
    ↓
Utils Layer               - Low-level Tool Functions
```

### Core Modules
- **apppro.py** - Main application entry (4,127 lines)
- **services/** - File services, knowledge base services, configuration services
- **processors/** - Document processors, web crawlers (15 modules)
- **ui/** - User interface components (30 modules)
- **utils/** - Utility function library (48 modules)
- **Total**: 180 Python files, 51 test files

---

## 🚀 Quick Start

### System Requirements
- **Python**: 3.8+ (Recommended 3.10+)
- **Memory**: 4GB+ (Recommended 8GB+)
- **Disk**: 10GB+ (Including model cache)
- **GPU**: Optional (CUDA/MPS support)

### Installation & Deployment

#### macOS/Linux Auto Installation
```bash
git clone https://github.com/zhaosj0315/rag-pro-max.git
cd rag-pro-max
./scripts/deploy_linux.sh  # Linux
pip install -r requirements.txt  # macOS
```

#### Windows Auto Installation
```cmd
git clone https://github.com/zhaosj0315/rag-pro-max.git
cd rag-pro-max
scripts\deploy_windows.bat
```

#### Docker Deployment
```bash
./scripts/docker-build.sh
docker-compose up -d
# Access: http://localhost:8501
```

### Launch Application
```bash
# Recommended (with tests)
./start.sh

# Direct launch
streamlit run src/apppro.py
```

---

## ⚙️ Configuration

### Model Configuration
Supports multiple LLM backends:
- **OpenAI**: GPT-3.5/GPT-4
- **Ollama**: Local models (qwen2.5:7b, etc.)
- **Others**: OpenAI-compatible interfaces

### Core Configuration Files
```
config/
├── app_config.json      # Application configuration
├── rag_config.json      # RAG parameters
└── scheduler_config.json # Scheduler configuration
```

---

## 🛡️ Enterprise Security & Compliance

### ✅ Suitable Scenarios
- **Financial Institutions**: Absolute confidentiality of customer data
- **Government Departments**: Secure processing of classified documents
- **Healthcare Organizations**: Strict protection of patient privacy
- **Manufacturing Enterprises**: Internal circulation of technical materials

### 🔐 Security Mechanisms
- **Zero Network Dependency**: Core functions require no internet
- **Data Sovereignty**: Document content strictly localized
- **Container Isolation**: Docker environment security isolation
- **Source Transparency**: Fully open source, security auditable

---

## 📊 Performance Benchmarks

### Processing Speed
| Document Type | Size | Processing Time | GPU Acceleration |
|---------------|------|----------------|------------------|
| PDF | 10MB | ~45s | ✅ 2-5x |
| DOCX | 5MB | ~20s | ✅ Auto |
| Web Pages | 100 pages | ~2min | ✅ Parallel |

### System Resources
| Scenario | CPU | GPU | Memory |
|----------|-----|-----|--------|
| Idle | 5-10% | 0% | 2-3GB |
| Processing | 60-85% | 99% | 10-15GB |
| Query | 10-20% | 50-70% | 5-8GB |

---

## 🧪 Testing & Validation

### Factory Testing
```bash
# Run complete tests
python tests/factory_test.py

# Test Coverage: 88/97 passed (92.8%)
# Test Categories: Environment, Configuration, Modules, Documents, Vector DB, etc.
```

---

## 📚 Documentation

- [📋 Deployment Guide](docs/en/DEPLOYMENT.md)
- [🧪 Testing Guide](docs/en/TESTING.md) 
- [❓ FAQ](docs/en/FAQ.md)
- [🤝 Contributing Guide](docs/en/CONTRIBUTING.md)
- [📝 Changelog](CHANGELOG.md)

---

## 📞 Contact & Support

- **GitHub**: https://github.com/zhaosj0315/rag-pro-max
- **Technical Support**: zhaosj0315@github.com
- **Business Cooperation**: Enterprise WeChat/DingTalk consultation
- **Deployment Services**: Professional implementation team available

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgments

Thanks to the following open source projects:
- [Streamlit](https://streamlit.io/) - Web application framework
- [LlamaIndex](https://www.llamaindex.ai/) - RAG framework
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [HuggingFace](https://huggingface.co/) - Model platform

---

<div align="center">

**If this project helps you, please give it a ⭐️ Star!**

Made with ❤️ by RAG Pro Max Team

</div>
