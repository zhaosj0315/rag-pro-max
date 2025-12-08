#!/bin/bash

echo "🐳 开始构建 RAG Pro Max Docker 镜像..."

# 构建镜像
docker build -t rag-pro-max:latest .

if [ $? -eq 0 ]; then
    echo "✅ 镜像构建成功！"
    echo ""
    echo "📦 镜像信息:"
    docker images | grep rag-pro-max
    echo ""
    echo "🚀 运行方式:"
    echo "  1. 使用 docker-compose: docker-compose up -d"
    echo "  2. 直接运行: docker run -p 8501:8501 -v \$(pwd)/vector_db_storage:/app/vector_db_storage rag-pro-max:latest"
    echo ""
    echo "🌐 访问地址: http://localhost:8501"
else
    echo "❌ 镜像构建失败"
    exit 1
fi
