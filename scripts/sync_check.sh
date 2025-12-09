#!/bin/bash
# 文档和代码同步检查脚本

echo "================================================================================"
echo "📋 文档和代码同步检查"
echo "================================================================================"

cd "$(dirname "$0")/.."

# 1. 检查版本号
echo ""
echo "1️⃣ 检查版本号"
echo "--------------------------------------------------------------------------------"
README_VERSION=$(grep -o 'version-[0-9.]*' README.md | head -1 | cut -d'-' -f2)
echo "README.md 版本: $README_VERSION"
echo "预期版本: 1.4.0 (Stage 6 完成)"

if [ "$README_VERSION" != "1.4.0" ]; then
    echo "⚠️ 版本号需要更新"
else
    echo "✅ 版本号正确"
fi

# 2. 检查测试脚本
echo ""
echo "2️⃣ 检查测试脚本"
echo "--------------------------------------------------------------------------------"
TEST_FILES=$(find tests -name "*.py" -type f | wc -l)
echo "测试文件数量: $TEST_FILES"

# 运行出厂测试
echo ""
echo "运行出厂测试..."
python3 tests/factory_test.py 2>&1 | tail -10

# 3. 检查新增模块
echo ""
echo "3️⃣ 检查新增模块"
echo "--------------------------------------------------------------------------------"
if [ -f "src/utils/parallel_executor.py" ]; then
    echo "✅ parallel_executor.py 存在"
else
    echo "❌ parallel_executor.py 缺失"
fi

if [ -f "src/utils/parallel_tasks.py" ]; then
    echo "✅ parallel_tasks.py 存在"
else
    echo "❌ parallel_tasks.py 缺失"
fi

if [ -f "tests/test_parallel_executor.py" ]; then
    echo "✅ test_parallel_executor.py 存在"
else
    echo "❌ test_parallel_executor.py 缺失"
fi

# 4. 检查文档
echo ""
echo "4️⃣ 检查文档"
echo "--------------------------------------------------------------------------------"
DOCS=(
    "docs/STAGE6_COMPLETE.md"
    "docs/STAGE6_PARALLEL_PLAN.md"
    "docs/AUTO_PARALLEL_GUIDE.md"
    "docs/PARALLEL_COMPARISON.md"
    "docs/QUEUE_OPTIMIZATION.md"
    "docs/STAGE5_3_COMPLETE.md"
    "docs/STAGE5_SUMMARY.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        echo "✅ $doc"
    else
        echo "❌ $doc 缺失"
    fi
done

# 5. 检查代码导入
echo ""
echo "5️⃣ 检查代码导入"
echo "--------------------------------------------------------------------------------"
echo "检查主文件导入..."
if grep -q "from src.utils.parallel_executor import ParallelExecutor" src/apppro.py; then
    echo "✅ 主文件已导入 ParallelExecutor"
else
    echo "❌ 主文件未导入 ParallelExecutor"
fi

if grep -q "from src.utils.parallel_tasks import" src/apppro.py; then
    echo "✅ 主文件已导入 parallel_tasks"
else
    echo "❌ 主文件未导入 parallel_tasks"
fi

echo ""
echo "检查 IndexBuilder 导入..."
if grep -q "from src.utils.parallel_executor import ParallelExecutor" src/processors/index_builder.py; then
    echo "✅ IndexBuilder 已导入 ParallelExecutor"
else
    echo "❌ IndexBuilder 未导入 ParallelExecutor"
fi

# 6. 检查旧代码是否清理
echo ""
echo "6️⃣ 检查旧代码清理"
echo "--------------------------------------------------------------------------------"
if grep -q "def _process_node_worker" src/apppro.py; then
    echo "⚠️ 主文件仍有 _process_node_worker 定义（应该已删除）"
else
    echo "✅ _process_node_worker 已移除"
fi

if grep -q "def _extract_metadata_task" src/apppro.py; then
    echo "⚠️ 主文件仍有 _extract_metadata_task 定义（应该已删除）"
else
    echo "✅ _extract_metadata_task 已移除"
fi

if grep -q "mp.Pool" src/processors/index_builder.py; then
    echo "⚠️ IndexBuilder 仍使用 mp.Pool（应该改用 ParallelExecutor）"
else
    echo "✅ mp.Pool 已替换"
fi

# 7. 总结
echo ""
echo "================================================================================"
echo "📊 检查总结"
echo "================================================================================"
echo ""
echo "请根据上述检查结果，更新相应的文档和代码。"
echo ""
