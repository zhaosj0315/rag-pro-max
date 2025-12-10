#!/bin/bash
# API服务管理脚本

case "$1" in
    start)
        echo "🚀 启动API服务器..."
        python start_api.py &
        echo $! > api.pid
        sleep 2
        if curl -s http://localhost:8000/health > /dev/null; then
            echo "✅ API服务器启动成功"
            echo "📡 API文档: http://localhost:8000/docs"
            echo "🔗 健康检查: http://localhost:8000/health"
        else
            echo "❌ API服务器启动失败"
        fi
        ;;
    stop)
        echo "🛑 停止API服务器..."
        if [ -f api.pid ]; then
            kill $(cat api.pid) 2>/dev/null
            rm -f api.pid
            echo "✅ API服务器已停止"
        else
            pkill -f "start_api.py"
            echo "✅ API服务器已强制停止"
        fi
        ;;
    status)
        if curl -s http://localhost:8000/health > /dev/null; then
            echo "✅ API服务器运行中"
            curl -s http://localhost:8000/health
        else
            echo "❌ API服务器未运行"
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    *)
        echo "用法: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac
