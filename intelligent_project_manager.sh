#!/bin/bash
"""
RAG Pro Max 智能项目管理器
一键运行项目分析、计划制定和自动执行
"""

PROJECT_ROOT="/Users/zhaosj/Documents/rag-pro-max"
cd "$PROJECT_ROOT" || exit 1

echo "🧠 RAG Pro Max 智能项目管理器"
echo "================================"

show_menu() {
    echo ""
    echo "请选择操作："
    echo "1) 🔍 智能项目分析"
    echo "2) 📋 生成工作计划"
    echo "3) 🚀 自动执行计划"
    echo "4) 📊 查看项目状态"
    echo "5) 🔄 完整优化循环"
    echo "6) ❌ 退出"
    echo ""
}

run_analysis() {
    echo "🔍 运行智能项目分析..."
    python3 smart_project_analyzer.py
    echo "✅ 分析完成"
}

generate_plan() {
    echo "📋 生成详细工作计划..."
    python3 intelligent_planner.py
    echo "✅ 计划生成完成"
}

execute_plan() {
    echo "🚀 自动执行工作计划..."
    python3 auto_plan_executor.py
    echo "✅ 计划执行完成"
}

show_status() {
    echo "📊 项目状态概览"
    echo "=================="
    
    # 代码统计
    echo "📁 代码文件数: $(find src -name '*.py' | wc -l)"
    echo "📄 总代码行数: $(find src -name '*.py' -exec wc -l {} + | tail -1 | awk '{print $1}')"
    
    # 最新计划
    latest_plan=$(ls -t work_plans/next_sprint_plan_*.md 2>/dev/null | head -1)
    if [ -n "$latest_plan" ]; then
        echo "📋 最新计划: $(basename "$latest_plan")"
        echo "📅 生成时间: $(stat -f "%Sm" "$latest_plan")"
    fi
    
    # 系统健康
    echo "💚 系统状态: $(python3 monitoring_system.py 2>/dev/null | grep '状态:' | cut -d' ' -f2 || echo '未知')"
}

run_full_cycle() {
    echo "🔄 运行完整优化循环..."
    echo ""
    
    echo "第1步: 智能分析项目"
    run_analysis
    echo ""
    
    echo "第2步: 生成工作计划"  
    generate_plan
    echo ""
    
    echo "第3步: 自动执行计划"
    execute_plan
    echo ""
    
    echo "第4步: 验证执行结果"
    python3 monitoring_system.py
    echo ""
    
    echo "🎉 完整优化循环完成！"
}

# 主循环
main() {
    while true; do
        show_menu
        read -p "请输入选择 (1-6): " choice
        
        case $choice in
            1)
                run_analysis
                ;;
            2)
                generate_plan
                ;;
            3)
                execute_plan
                ;;
            4)
                show_status
                ;;
            5)
                run_full_cycle
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

# 检查依赖
check_dependencies() {
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 未找到"
        exit 1
    fi
    
    # 检查核心脚本
    scripts=("smart_project_analyzer.py" "intelligent_planner.py" "auto_plan_executor.py" "monitoring_system.py")
    for script in "${scripts[@]}"; do
        if [ ! -f "$script" ]; then
            echo "❌ 缺少脚本: $script"
            exit 1
        fi
    done
}

# 初始化
init_project() {
    echo "🔧 初始化项目管理环境..."
    
    # 创建必要目录
    mkdir -p work_plans
    mkdir -p monitoring_alerts
    mkdir -p prompt_templates
    
    echo "✅ 环境初始化完成"
}

# 启动检查
check_dependencies
init_project

# 运行主程序
main
