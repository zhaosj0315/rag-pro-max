#!/usr/bin/env python3
"""自动替换 terminal_logger 为 logger"""

import re

# 读取文件
with open('src/apppro.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 替换导入
content = content.replace(
    'from src.terminal_logger import terminal_logger',
    '# terminal_logger 已被 logger 替代'
)

# 2. 替换所有 terminal_logger 调用为 logger
replacements = [
    (r'terminal_logger\.info\(', 'logger.info('),
    (r'terminal_logger\.success\(', 'logger.success('),
    (r'terminal_logger\.warning\(', 'logger.warning('),
    (r'terminal_logger\.error\(', 'logger.error('),
    (r'terminal_logger\.debug\(', 'logger.debug('),
    (r'terminal_logger\.separator\(', 'logger.separator('),
    (r'terminal_logger\.start_operation\(', 'logger.start_operation('),
    (r'terminal_logger\.processing\(', 'logger.processing('),
    (r'terminal_logger\.complete_operation\(', 'logger.complete_operation('),
    (r'terminal_logger\.data_summary\(', 'logger.data_summary('),
    (r'terminal_logger\.timer\(', 'logger.timer('),
]

for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

# 写回文件
with open('src/apppro.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 已替换所有 terminal_logger 调用")
print(f"📝 共替换 {sum(len(re.findall(pattern, content)) for pattern, _ in replacements)} 处")
