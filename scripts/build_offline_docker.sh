#!/bin/bash
# RAG Pro Max 离线Docker镜像构建脚本

set -e

echo "🐳 构建RAG Pro Max离线完整镜像..."
echo "=================================================="

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 设置镜像信息
IMAGE_NAME="rag-pro-max-offline"
VERSION="v2.4.1"
FULL_NAME="${IMAGE_NAME}:${VERSION}"

echo "📦 镜像信息:"
echo "  名称: ${IMAGE_NAME}"
echo "  版本: ${VERSION}"
echo "  完整名称: ${FULL_NAME}"
echo ""

# 检查磁盘空间 (需要至少20GB)
echo "💾 检查磁盘空间..."
AVAILABLE_SPACE=$(df . | tail -1 | awk '{print $4}')
REQUIRED_SPACE=20971520  # 20GB in KB

if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
    echo "⚠️ 警告: 可用磁盘空间不足20GB，构建可能失败"
    echo "  当前可用: $(($AVAILABLE_SPACE / 1024 / 1024))GB"
    echo "  建议最少: 20GB"
    read -p "是否继续? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p data/{vector_db,chat_histories,app_logs}

# 构建镜像
echo "🔨 开始构建镜像 (预计需要30-60分钟)..."
echo "  - 下载基础镜像和依赖"
echo "  - 安装Ollama和下载qwen2.5:7b模型"
echo "  - 下载HuggingFace嵌入模型"
echo "  - 配置应用环境"
echo ""

# 记录开始时间
START_TIME=$(date +%s)

# 构建镜像
docker build \
    -f Dockerfile.offline \
    -t "${FULL_NAME}" \
    -t "${IMAGE_NAME}:latest" \
    --progress=plain \
    .

# 计算构建时间
END_TIME=$(date +%s)
BUILD_TIME=$((END_TIME - START_TIME))
BUILD_MINUTES=$((BUILD_TIME / 60))
BUILD_SECONDS=$((BUILD_TIME % 60))

echo ""
echo "✅ 镜像构建完成!"
echo "  构建时间: ${BUILD_MINUTES}分${BUILD_SECONDS}秒"

# 显示镜像信息
echo ""
echo "📊 镜像信息:"
docker images "${IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# 显示镜像大小
IMAGE_SIZE=$(docker images "${FULL_NAME}" --format "{{.Size}}")
echo ""
echo "💾 镜像大小: ${IMAGE_SIZE}"

# 保存镜像到文件 (可选)
echo ""
read -p "是否导出镜像到tar文件? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📦 导出镜像到文件..."
    docker save "${FULL_NAME}" | gzip > "${IMAGE_NAME}-${VERSION}.tar.gz"
    echo "✅ 镜像已导出到: ${IMAGE_NAME}-${VERSION}.tar.gz"
    
    # 显示文件大小
    FILE_SIZE=$(ls -lh "${IMAGE_NAME}-${VERSION}.tar.gz" | awk '{print $5}')
    echo "  文件大小: ${FILE_SIZE}"
fi

echo ""
echo "🚀 使用方法:"
echo "  1. 启动容器:"
echo "     docker-compose -f docker-compose.offline.yml up -d"
echo ""
echo "  2. 访问应用:"
echo "     http://localhost:8501"
echo ""
echo "  3. 查看日志:"
echo "     docker logs -f rag-pro-max-offline"
echo ""
echo "  4. 停止服务:"
echo "     docker-compose -f docker-compose.offline.yml down"

echo ""
echo "🎉 RAG Pro Max离线版构建完成!"
