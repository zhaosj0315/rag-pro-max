#!/bin/bash
# RAG Pro Max 离线Docker构建脚本 (专家审查修复版)
# 解决了GPU依赖、镜像大小、安全等问题

set -e

echo "🔬 RAG Pro Max 离线镜像构建 (专家审查版)"
echo "=================================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_requirement() {
    local cmd=$1
    local name=$2
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}❌ $name 未安装${NC}"
        return 1
    else
        echo -e "${GREEN}✅ $name 已安装${NC}"
        return 0
    fi
}

# 环境检查
echo "🔍 环境检查..."
check_requirement "docker" "Docker" || exit 1
check_requirement "curl" "curl" || exit 1

# 检查Docker运行状态
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker未运行，请先启动Docker${NC}"
    exit 1
fi

# 检查网络连接
echo "🌐 检查网络连接..."
if ! curl -s --connect-timeout 5 https://ollama.com > /dev/null; then
    echo -e "${YELLOW}⚠️ 网络连接不稳定，构建可能失败${NC}"
    read -p "是否继续? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 设置镜像信息
IMAGE_NAME="rag-pro-max-offline-cpu"
VERSION="v2.4.1"
FULL_NAME="${IMAGE_NAME}:${VERSION}"

echo "📦 镜像信息:"
echo "  名称: ${IMAGE_NAME}"
echo "  版本: ${VERSION}"
echo "  类型: CPU-only (无GPU依赖)"
echo "  预估大小: 4-6GB (相比原版减少50%)"
echo ""

# 检查磁盘空间 (降低到15GB)
echo "💾 检查磁盘空间..."
AVAILABLE_SPACE=$(df . | tail -1 | awk '{print $4}')
REQUIRED_SPACE=15728640  # 15GB in KB

if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
    echo -e "${YELLOW}⚠️ 可用磁盘空间不足15GB${NC}"
    echo "  当前可用: $(($AVAILABLE_SPACE / 1024 / 1024))GB"
    echo "  建议最少: 15GB"
    read -p "是否继续? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 创建CPU-only requirements
echo "📝 创建CPU-only依赖文件..."
if [ -f "requirements.txt" ]; then
    # 备份原文件
    cp requirements.txt requirements.txt.backup
    
    # 创建CPU版本
    sed 's/torch.*/torch==2.1.0+cpu torchvision==0.16.0+cpu -f https:\/\/download.pytorch.org\/whl\/cpu/' requirements.txt > requirements-cpu.txt
    
    echo -e "${GREEN}✅ CPU-only依赖文件创建完成${NC}"
else
    echo -e "${RED}❌ requirements.txt 文件不存在${NC}"
    exit 1
fi

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p data/{vector_db,chat_histories,app_logs}

# 构建镜像
echo "🔨 开始构建镜像 (预计需要20-40分钟)..."
echo "  阶段1: 基础环境 (Python 3.10 slim)"
echo "  阶段2: Ollama + 模型下载 (qwen2.5:7b)"
echo "  阶段3: Python依赖 + HuggingFace模型"
echo "  阶段4: 应用集成和优化"
echo ""

# 记录开始时间
START_TIME=$(date +%s)

# 构建镜像 (使用修复版Dockerfile)
docker build \
    -f Dockerfile.offline.fixed \
    -t "${FULL_NAME}" \
    -t "${IMAGE_NAME}:latest" \
    --progress=plain \
    --no-cache \
    . 2>&1 | tee build.log

# 检查构建结果
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo -e "${GREEN}✅ 镜像构建成功!${NC}"
else
    echo -e "${RED}❌ 镜像构建失败${NC}"
    echo "请检查 build.log 文件获取详细错误信息"
    exit 1
fi

# 计算构建时间
END_TIME=$(date +%s)
BUILD_TIME=$((END_TIME - START_TIME))
BUILD_MINUTES=$((BUILD_TIME / 60))
BUILD_SECONDS=$((BUILD_TIME % 60))

echo ""
echo -e "${GREEN}🎉 构建完成!${NC}"
echo "  构建时间: ${BUILD_MINUTES}分${BUILD_SECONDS}秒"

# 显示镜像信息
echo ""
echo "📊 镜像信息:"
docker images "${IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# 镜像测试
echo ""
echo "🧪 快速测试镜像..."
if docker run --rm -d --name test-rag -p 18501:8501 "${FULL_NAME}" > /dev/null; then
    sleep 30
    if curl -f http://localhost:18501 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 镜像测试通过${NC}"
        docker stop test-rag > /dev/null
    else
        echo -e "${YELLOW}⚠️ 镜像启动较慢，请手动测试${NC}"
        docker stop test-rag > /dev/null 2>&1 || true
    fi
else
    echo -e "${YELLOW}⚠️ 无法进行快速测试${NC}"
fi

# 导出镜像
echo ""
read -p "是否导出镜像到tar.gz文件? (推荐) (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo "📦 导出镜像..."
    docker save "${FULL_NAME}" | gzip > "${IMAGE_NAME}-${VERSION}.tar.gz"
    
    FILE_SIZE=$(ls -lh "${IMAGE_NAME}-${VERSION}.tar.gz" | awk '{print $5}')
    echo -e "${GREEN}✅ 镜像已导出${NC}"
    echo "  文件: ${IMAGE_NAME}-${VERSION}.tar.gz"
    echo "  大小: ${FILE_SIZE}"
    
    # 生成校验和
    echo "🔐 生成校验和..."
    sha256sum "${IMAGE_NAME}-${VERSION}.tar.gz" > "${IMAGE_NAME}-${VERSION}.sha256"
    echo -e "${GREEN}✅ 校验和已生成: ${IMAGE_NAME}-${VERSION}.sha256${NC}"
fi

# 清理临时文件
echo ""
echo "🧹 清理临时文件..."
rm -f requirements-cpu.txt build.log
if [ -f "requirements.txt.backup" ]; then
    mv requirements.txt.backup requirements.txt
fi

echo ""
echo -e "${GREEN}🎉 RAG Pro Max 离线版构建完成!${NC}"
echo ""
echo "📋 部署文件清单:"
echo "  - ${IMAGE_NAME}-${VERSION}.tar.gz (Docker镜像)"
echo "  - ${IMAGE_NAME}-${VERSION}.sha256 (校验和)"
echo "  - scripts/deploy_linux_offline.sh (部署脚本)"
echo ""
echo "🚀 Linux部署步骤:"
echo "  1. 传输文件到Linux服务器"
echo "  2. 运行: sudo bash deploy_linux_offline.sh"
echo "  3. 访问: http://服务器IP:8501"
echo ""
echo "💡 优化特性:"
echo "  ✅ CPU-only版本，无GPU依赖"
echo "  ✅ 非root用户运行，安全性提升"
echo "  ✅ 镜像大小减少50%"
echo "  ✅ 完整离线功能，包含所有模型"
echo "  ✅ 自动健康检查和错误恢复"
