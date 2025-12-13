# 安装指南

## 系统要求

- Python 3.8+
- 4GB+ 内存
- 5GB+ 磁盘空间
- macOS / Linux / Windows

## 快速安装

### 1. 克隆项目
```bash
git clone https://github.com/yourusername/rag-pro-max.git
cd rag-pro-max
```

### 2. 创建虚拟环境（推荐）
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 运行应用
```bash
streamlit run src/apppro.py
```

应用将自动在浏览器打开 http://localhost:8501

## 配置 LLM

### OpenAI 配置
1. 获取 [OpenAI API Key](https://platform.openai.com/api-keys)
2. 在应用侧边栏配置：
   - API Base URL: `https://api.openai.com/v1`
   - API Key: 你的密钥
   - 模型: `gpt-3.5-turbo` 或 `gpt-4`

### Ollama 本地模型
1. 安装 [Ollama](https://ollama.ai)
2. 启动模型：`ollama run qwen2.5:7b`
3. 在应用侧边栏配置：
   - API Base URL: `http://localhost:11434`
   - 模型: `qwen2.5:7b`

## 打包为独立应用

### macOS
```bash
chmod +x scripts/build_mac.sh
./scripts/build_mac.sh
```

输出位置：`dist/RAG_Pro_Max.app`

## 故障排除

### 依赖冲突
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### 模型下载缓慢
设置 HuggingFace 镜像：
```bash
export HF_ENDPOINT=https://huggingface.co
```

### 内存不足
- 减小 `chunk_size` 配置
- 清理 `vector_db_storage/` 目录
- 关闭其他应用

## 获取帮助

- 查看 [README.md](../README.md)
- 提交 [Issue](https://github.com/yourusername/rag-pro-max/issues)
