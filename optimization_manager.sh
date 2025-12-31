#!/bin/bash
"""
RAG Pro Max 持续优化系统 - 一键启动脚本
"""

PROJECT_ROOT="/Users/zhaosj/Documents/rag-pro-max"
cd "$PROJECT_ROOT" || exit 1

echo "🚀 RAG Pro Max 持续优化系统"
echo "================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未找到，请先安装Python3"
    exit 1
fi

# 显示菜单
show_menu() {
    echo ""
    echo "请选择操作："
    echo "1) 🔄 运行单次优化循环"
    echo "2) 📊 启动优化仪表板"
    echo "3) ⚙️ 设置定时任务"
    echo "4) 📋 查看最新报告"
    echo "5) 🧹 清理旧报告"
    echo "6) ❌ 退出"
    echo ""
}

# 运行优化循环
run_optimization() {
    echo "🔄 正在运行优化循环..."
    python3 continuous_optimization_system.py
    echo "✅ 优化循环完成"
}

# 启动仪表板
start_dashboard() {
    echo "📊 启动优化仪表板..."
    echo "浏览器将打开 http://localhost:8502"
    streamlit run optimization_dashboard.py --server.port 8502
}

# 设置定时任务
setup_cron() {
    echo "⚙️ 设置定时任务..."
    
    # 检查是否已存在
    if crontab -l 2>/dev/null | grep -q "optimization_scheduler.sh"; then
        echo "⚠️ 定时任务已存在"
        return
    fi
    
    # 添加定时任务
    (crontab -l 2>/dev/null; echo "0 2 * * * $PROJECT_ROOT/optimization_scheduler.sh") | crontab -
    echo "✅ 定时任务已设置 (每天凌晨2点运行)"
}

# 查看最新报告
view_latest_report() {
    echo "📋 查看最新报告..."
    
    latest_report=$(ls -t optimization_reports/optimization_report_*.json 2>/dev/null | head -1)
    
    if [ -z "$latest_report" ]; then
        echo "❌ 未找到报告文件"
        return
    fi
    
    echo "最新报告: $latest_report"
    echo "----------------------------------------"
    
    # 提取关键信息
    python3 -c "
import json
with open('$latest_report', 'r') as f:
    data = json.load(f)
    
summary = data.get('summary', {})
print(f\"📊 报告摘要:\")
print(f\"  生成时间: {data.get('timestamp', 'N/A')}\"[:19])
print(f\"  发现问题: {summary.get('issues_found', 0)} 个\")
print(f\"  创建任务: {summary.get('tasks_created', 0)} 个\")
print(f\"  完成任务: {summary.get('tasks_completed', 0)} 个\")

issues = data.get('issues', [])
if issues:
    print(f\"\\n⚠️ 主要问题:\")
    for issue in issues[:3]:
        print(f\"  - {issue.get('description', 'N/A')}\")
"
}

# 清理旧报告
cleanup_reports() {
    echo "🧹 清理30天前的旧报告..."
    
    count=$(find optimization_reports -name "optimization_report_*.json" -mtime +30 | wc -l)
    find optimization_reports -name "optimization_report_*.json" -mtime +30 -delete
    
    echo "✅ 已清理 $count 个旧报告"
}

# 主循环
main() {
    while true; do
        show_menu
        read -p "请输入选择 (1-6): " choice
        
        case $choice in
            1)
                run_optimization
                ;;
            2)
                start_dashboard
                ;;
            3)
                setup_cron
                ;;
            4)
                view_latest_report
                ;;
            5)
                cleanup_reports
                ;;
            6)
                echo "👋 再见！"
                exit 0
                ;;
            *)
                echo "❌ 无效选择，请重新输入"
                ;;
        esac
        
        echo ""
        read -p "按回车键继续..."
    done
}

# 运行主程序
main
