# RAG Pro Max

企业级 RAG (Retrieval Augmented Generation) 知识库系统

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
./start.sh
# 或
streamlit run src/apppro.py
```

## 核心功能

- 📄 多格式文档处理 (PDF, DOCX, TXT等)
- 🖼️ 图片OCR识别
- 🔍 智能语义检索
- 💬 多轮对话
- 🌐 网页内容抓取
- 🔄 持续优化系统

## 项目结构

```
├── src/                # 源代码
├── scripts/            # 部署脚本
├── config/             # 配置文件
├── tests/              # 测试文件
├── docs/               # 文档
└── requirements.txt    # 依赖包
```

## 配置

主要配置文件：
- `config/app_config.json` - 应用配置
- `config/rag_config.json` - RAG参数
- `.streamlit/config.toml` - Streamlit配置

## 部署

### Docker
```bash
docker-compose up -d
```

### 本地部署
```bash
# Linux/macOS
./scripts/deploy_linux.sh

# Windows
scripts\deploy_windows.bat
```

## 文档

- [部署指南](DEPLOYMENT.md)
- [用户手册](USER_MANUAL.md)
- [API文档](API_DOCUMENTATION.md)
- [常见问题](FAQ.md)

## 许可证

MIT License - 详见 [LICENSE](LICENSE)
