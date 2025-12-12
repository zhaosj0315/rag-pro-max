#!/bin/bash

echo "⚡ 切换到快速模式（跳过OCR）"

# 设置环境变量
export SKIP_OCR=true

echo "✅ 已设置 SKIP_OCR=true"
echo "🚀 现在重新处理知识库将跳过扫描版PDF OCR"
echo ""
echo "💡 在当前终端中运行："
echo "   export SKIP_OCR=true"
echo "   然后重新上传文档即可"
