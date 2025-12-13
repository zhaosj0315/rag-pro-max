#!/bin/bash
# 清理过程代码脚本

echo "🧹 开始清理过程代码..."

# 创建备份目录
mkdir -p archive/code_backup_$(date +%Y%m%d)
BACKUP_DIR="archive/code_backup_$(date +%Y%m%d)"

echo "📦 备份过程代码到: $BACKUP_DIR"

# 备份src目录下的备份文件
echo "🔄 清理src目录备份文件..."
find src -name "*.backup*" -exec mv {} $BACKUP_DIR/ \;
find src -name "*backup*.py" -exec mv {} $BACKUP_DIR/ \;
find src -name "*old*.py" -exec mv {} $BACKUP_DIR/ \;

# 备份多版本app文件（保留主要的4个版本）
echo "🔄 清理多版本app文件..."
mv src/apppro_backup_*.py $BACKUP_DIR/ 2>/dev/null
mv src/apppro_full_backup.py $BACKUP_DIR/ 2>/dev/null
mv src/apppro_step*.py $BACKUP_DIR/ 2>/dev/null
mv src/apppro_v*.py $BACKUP_DIR/ 2>/dev/null

# 备份根目录临时Python文件（保留重要的）
echo "🔄 清理根目录临时文件..."
# 保留重要文件，移动其他临时文件
for file in *.py; do
    if [[ "$file" != "kbllama" && "$file" != "show_logs.py" && "$file" != "view_logs.py" && "$file" != "system_monitor.py" ]]; then
        mv "$file" $BACKUP_DIR/ 2>/dev/null
    fi
done

# 清理临时目录和缓存
echo "🗑️ 清理临时目录..."
rm -rf __pycache__/ 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null
find . -name ".DS_Store" -delete 2>/dev/null

# 清理空的__pycache__目录
find . -type d -name "__pycache__" -empty -delete 2>/dev/null

echo "✅ 代码清理完成！"
echo "📊 清理统计:"
echo "   - 备份文件: $(ls $BACKUP_DIR 2>/dev/null | wc -l) 个"
echo "   - 剩余根目录Python文件: $(ls *.py 2>/dev/null | wc -l) 个"
echo "   - 备份位置: $BACKUP_DIR"

# 显示保留的重要文件
echo "📋 保留的重要Python文件:"
ls *.py 2>/dev/null | head -5
