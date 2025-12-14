#!/bin/bash
# RAG Pro Max 实例管理脚本

show_instances() {
    echo "📋 当前运行的 RAG Pro Max 实例:"
    echo "----------------------------------------"
    
    ps aux | grep "streamlit run src/apppro.py" | grep -v grep | while IFS= read -r line; do
        pid=$(echo $line | awk '{print $2}')
        port=$(echo $line | grep -o -- '--server.port [0-9]*' | awk '{print $2}')
        if [ -z "$port" ]; then
            port="8501"  # 默认端口
        fi
        echo "🚀 PID: $pid | 端口: $port | 访问: http://localhost:$port"
    done
    
    echo "----------------------------------------"
}

start_new_instance() {
    echo "🚀 启动新实例..."
    ./start_new_instance.sh
}

case "$1" in
    "list"|"ls"|"")
        show_instances
        ;;
    "new"|"start")
        start_new_instance
        ;;
    "help"|"-h"|"--help")
        echo "RAG Pro Max 实例管理"
        echo ""
        echo "用法:"
        echo "  ./manage_instances.sh [命令]"
        echo ""
        echo "命令:"
        echo "  list, ls     显示运行中的实例 (默认)"
        echo "  new, start   启动新实例"
        echo "  help         显示帮助"
        ;;
    *)
        echo "❌ 未知命令: $1"
        echo "使用 './manage_instances.sh help' 查看帮助"
        ;;
esac
