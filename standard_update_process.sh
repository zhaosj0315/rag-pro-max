#!/bin/bash
# 标准更新流程脚本

echo "🚀 执行标准更新流程..."
echo "=================================================="

# 1. 代码质量检查
echo "1️⃣ 代码质量检查..."
echo "--------------------------------------------------"
echo "📋 运行出厂测试..."
python tests/factory_test.py
if [ $? -ne 0 ]; then
    echo "❌ 出厂测试失败"
    exit 1
fi

echo "✅ 出厂测试通过"
echo ""

# 2. 文档一致性检查
echo "2️⃣ 文档一致性检查..."
echo "--------------------------------------------------"
python tools/doc_consistency_check.py
if [ $? -ne 0 ]; then
    echo "❌ 文档一致性检查失败"
    exit 1
fi

echo "✅ 文档一致性检查通过"
echo ""

# 3. 可行性测试
echo "3️⃣ 可行性测试..."
echo "--------------------------------------------------"
echo "📋 运行文档可行性测试..."
python tests/test_documentation_feasibility.py
if [ $? -ne 0 ]; then
    echo "❌ 文档可行性测试失败"
    exit 1
fi

echo "✅ 可行性测试通过"
echo ""

# 4. 推送前检查
echo "4️⃣ 推送前检查..."
echo "--------------------------------------------------"
chmod +x check_before_push.sh
./check_before_push.sh
if [ $? -ne 0 ]; then
    echo "❌ 推送前检查失败"
    exit 1
fi

echo "✅ 推送前检查通过"
echo ""

# 5. 生成统计报告
echo "5️⃣ 生成统计报告..."
echo "--------------------------------------------------"
echo "📊 项目统计:"
echo "Python文件: $(find src -name '*.py' | wc -l | tr -d ' ')"
echo "代码行数: $(find src -name '*.py' -exec wc -l {} + | tail -1 | awk '{print $1}')"
echo "测试文件: $(find tests -name 'test_*.py' | wc -l | tr -d ' ')"
echo "文档文件: $(find . -maxdepth 1 -name '*.md' | wc -l | tr -d ' ')"
echo ""

# 6. 完成提示
echo "=================================================="
echo "🎉 标准流程完成！"
echo ""
echo "📋 检查结果:"
echo "✅ 出厂测试通过"
echo "✅ 文档一致性通过"
echo "✅ 可行性测试通过"
echo "✅ 推送前检查通过"
echo ""
echo "🚀 可以安全推送代码"
echo "=================================================="
