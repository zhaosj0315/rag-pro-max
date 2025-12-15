"""
RAG Pro Max - 重构后的主应用入口
精简版主文件，所有功能模块化
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.app.main_app import MainApp


def main():
    """主函数"""
    app = MainApp()
    app.run()


if __name__ == "__main__":
    main()
