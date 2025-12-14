#!/bin/bash
# 智能 RAG 启动脚本 - 自动端口检测

echo "🚀 RAG Pro Max 智能启动..."

# 端口检测函数
find_ports() {
    local streamlit_port=8501
    local api_port=8000
    
    # 检测 Streamlit 端口
    while [ $streamlit_port -le 8510 ]; do
        if ! lsof -i :$streamlit_port >/dev/null 2>&1; then
            break
        fi
        ((streamlit_port++))
    done
    
    # 检测 API 端口
    while [ $api_port -le 8010 ]; do
        if ! lsof -i :$api_port >/dev/null 2>&1; then
            break
        fi
        ((api_port++))
    done
    
    echo "$streamlit_port $api_port"
}

# 获取可用端口
ports=($(find_ports))
STREAMLIT_PORT=${ports[0]}
API_PORT=${ports[1]}

echo "🌐 Streamlit 端口: $STREAMLIT_PORT"
echo "🔌 API 端口: $API_PORT"
echo "📱 访问地址: http://localhost:$STREAMLIT_PORT"

# 启动应用
streamlit run src/apppro.py --server.port $STREAMLIT_PORT
