#!/usr/bin/env python3
"""优化启动脚本"""

import os
import warnings

# 设置环境变量
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# 忽略特定警告
warnings.filterwarnings("ignore", category=UserWarning, module="jieba")
warnings.filterwarnings("ignore", message=".*validate_default.*")
warnings.filterwarnings("ignore", message=".*pkg_resources.*")

# 启动应用
if __name__ == "__main__":
    import streamlit.web.cli as stcli
    import sys
    
    sys.argv = ["streamlit", "run", "src/apppro.py"]
    stcli.main()
