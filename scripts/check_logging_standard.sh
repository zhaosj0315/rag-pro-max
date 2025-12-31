#!/bin/bash
# 日志管理规范检查脚本
# 检查项目日志覆盖率和用户提醒质量

echo "🔍 RAG Pro Max 日志管理规范检查"
echo "================================"

# 1. 检查日志管理器使用情况
echo "📊 1. 日志管理器使用分析"
echo "------------------------"

# 统计 LogManager 使用
logmanager_count=$(grep -r "LogManager" src/ --include="*.py" | wc -l)
echo "✅ LogManager 使用次数: $logmanager_count"

# 检查直接使用 logging 的文件（可能需要迁移）
echo "⚠️ 直接使用 logging 模块的文件:"
direct_logging=$(grep -r "import logging" src/ --include="*.py" | grep -v "# 允许使用" | wc -l)
if [ $direct_logging -gt 0 ]; then
    grep -r "import logging" src/ --include="*.py" | grep -v "# 允许使用" | head -5
    echo "   发现 $direct_logging 个文件，建议迁移到 LogManager"
else
    echo "   ✅ 所有文件都使用统一的 LogManager"
fi

# 2. 用户提醒覆盖率统计
echo ""
echo "💬 2. 用户提醒使用统计"
echo "--------------------"
info_count=$(grep -r 'st\.info' src/ --include='*.py' | wc -l)
warning_count=$(grep -r 'st\.warning' src/ --include='*.py' | wc -l)
error_count=$(grep -r 'st\.error' src/ --include='*.py' | wc -l)
success_count=$(grep -r 'st\.success' src/ --include='*.py' | wc -l)
toast_count=$(grep -r 'st\.toast' src/ --include='*.py' | wc -l)

echo "📝 st.info:    $info_count 次使用"
echo "⚠️ st.warning: $warning_count 次使用"
echo "❌ st.error:   $error_count 次使用"
echo "✅ st.success: $success_count 次使用"
echo "🍞 st.toast:   $toast_count 次使用"

total_notifications=$((info_count + warning_count + error_count + success_count + toast_count))
echo "📊 总计用户提醒: $total_notifications 次"

# 3. 错误处理覆盖率
echo ""
echo "🛡️ 3. 错误处理覆盖率"
echo "------------------"
try_count=$(grep -r 'try:' src/ --include='*.py' | wc -l)
except_count=$(grep -r 'except' src/ --include='*.py' | wc -l)
echo "🔄 try 语句: $try_count 个"
echo "🚨 except 语句: $except_count 个"

if [ $try_count -gt 0 ]; then
    coverage_ratio=$((except_count * 100 / try_count))
    echo "📈 异常处理覆盖率: $coverage_ratio%"
else
    echo "⚠️ 未发现 try-except 语句"
fi

# 4. 性能监控检查
echo ""
echo "⏱️ 4. 性能监控使用情况"
echo "--------------------"
timer_count=$(grep -r 'timer(' src/ --include='*.py' | wc -l)
progress_count=$(grep -r 'progress' src/ --include='*.py' | wc -l)
status_count=$(grep -r 'st\.status' src/ --include='*.py' | wc -l)

echo "⏲️ 计时器使用: $timer_count 次"
echo "📊 进度显示: $progress_count 次"
echo "📋 状态显示: $status_count 次"

# 5. 关键业务流程检查
echo ""
echo "🔍 5. 关键业务流程日志检查"
echo "------------------------"

# 检查关键函数是否有日志记录
echo "检查关键函数的日志覆盖情况:"

# 文档处理函数
doc_process_funcs=$(grep -r "def.*process.*doc" src/ --include="*.py" | wc -l)
echo "📄 文档处理函数: $doc_process_funcs 个"

# 知识库操作函数  
kb_funcs=$(grep -r "def.*kb\|def.*knowledge" src/ --include="*.py" | wc -l)
echo "📚 知识库函数: $kb_funcs 个"

# 查询处理函数
query_funcs=$(grep -r "def.*query\|def.*search" src/ --include="*.py" | wc -l)
echo "🔍 查询函数: $query_funcs 个"

# 6. 消息格式规范检查
echo ""
echo "📝 6. 消息格式规范检查"
echo "--------------------"

# 检查是否使用了标准图标
standard_icons=("💡" "⚠️" "❌" "✅" "🔄" "⏳")
for icon in "${standard_icons[@]}"; do
    count=$(grep -r "$icon" src/ --include="*.py" | wc -l)
    echo "$icon 图标使用: $count 次"
done

# 7. 建议改进项
echo ""
echo "💡 7. 改进建议"
echo "------------"

if [ $direct_logging -gt 0 ]; then
    echo "🔧 建议将 $direct_logging 个文件迁移到 LogManager"
fi

if [ $timer_count -lt 10 ]; then
    echo "⏱️ 建议为更多关键操作添加性能监控"
fi

if [ $status_count -lt 5 ]; then
    echo "📋 建议为长时间操作添加状态显示"
fi

# 8. 总体评分
echo ""
echo "📊 8. 日志管理质量评分"
echo "--------------------"

score=0

# LogManager 使用率 (30分)
if [ $logmanager_count -gt 50 ]; then
    score=$((score + 30))
elif [ $logmanager_count -gt 20 ]; then
    score=$((score + 20))
else
    score=$((score + 10))
fi

# 用户提醒丰富度 (25分)
if [ $total_notifications -gt 200 ]; then
    score=$((score + 25))
elif [ $total_notifications -gt 100 ]; then
    score=$((score + 20))
else
    score=$((score + 15))
fi

# 错误处理覆盖率 (25分)
if [ $coverage_ratio -gt 80 ]; then
    score=$((score + 25))
elif [ $coverage_ratio -gt 60 ]; then
    score=$((score + 20))
else
    score=$((score + 15))
fi

# 性能监控使用 (20分)
monitor_total=$((timer_count + status_count))
if [ $monitor_total -gt 20 ]; then
    score=$((score + 20))
elif [ $monitor_total -gt 10 ]; then
    score=$((score + 15))
else
    score=$((score + 10))
fi

echo "🎯 总体评分: $score/100"

if [ $score -ge 80 ]; then
    echo "🏆 优秀 - 日志管理规范执行良好"
elif [ $score -ge 60 ]; then
    echo "👍 良好 - 有改进空间"
else
    echo "⚠️ 需要改进 - 建议按规范优化"
fi

echo ""
echo "📋 检查完成！详细规范请参考 LOGGING_AND_NOTIFICATION_STANDARD.md"
