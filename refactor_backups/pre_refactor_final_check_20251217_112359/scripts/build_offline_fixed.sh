#!/bin/bash

echo "🔬 RAG Pro Max 离线镜像构建 (修复版)"
echo "=================================================="

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装"
    exit 1
fi

echo "✅ Docker 已安装"

# 创建简化的Dockerfile
cat > Dockerfile.offline.simple << 'EOF'
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制应用代码
COPY . /app/

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 下载HuggingFace模型
RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-zh-v1.5')"

# 暴露端口
EXPOSE 8501

# 启动命令
CMD ["streamlit", "run", "src/apppro.py", "--server.address=0.0.0.0"]
EOF

echo "📝 创建简化Dockerfile完成"

# 构建镜像
echo "🔨 开始构建简化镜像..."
docker build -f Dockerfile.offline.simple -t rag-pro-max-offline-simple:v2.4.1 .

if [ $? -eq 0 ]; then
    echo "✅ 镜像构建成功"
    echo "📊 镜像信息:"
    docker images | grep rag-pro-max-offline-simple
    
    echo -e "\n🚀 启动命令:"
    echo "docker run -p 8501:8501 rag-pro-max-offline-simple:v2.4.1"
else
    echo "❌ 镜像构建失败"
    exit 1
fi
