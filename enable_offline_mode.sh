#!/bin/bash
echo "🔒 启用离线模式..."

# 设置离线环境变量
export OFFLINE_MODE=true
export DISABLE_OPENAI=true
export USE_LOCAL_LLM=true
export DISABLE_QUERY_REWRITE=true
export DISABLE_SUGGESTIONS=true

# 检查Ollama是否运行
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama未运行，启动Ollama..."
    ollama serve &
    sleep 3
    
    # 检查模型是否存在
    if ! ollama list | grep -q "qwen2.5:7b"; then
        echo "📥 下载本地模型..."
        ollama pull qwen2.5:7b
    fi
fi

echo "✅ 离线模式配置完成"
echo "🚀 重启应用..."

# 停止当前应用
pkill -f "streamlit run"
sleep 2

# 启动离线模式应用
cd /Users/zhaosj/Documents/rag-pro-max
streamlit run src/apppro.py --server.headless=true &

echo "✅ 离线应用已启动"
