# 初始化环境配置
import warnings
# 极其早地抑制 Pydantic 警告，防止第三方库加载时触发
warnings.filterwarnings("ignore", category=UserWarning, message=".*UnsupportedFieldAttributeWarning.*")
warnings.filterwarnings("ignore", message=".*validate_default.*")

# [v4.2.1] 多进程安全入口保护 - 更加优雅的拦截方式
def check_multiprocessing():
    import sys
    if __name__ != "__main__":
        # 如果是子进程，静默返回而不崩溃应用
        return False
    return True

if not check_multiprocessing():
    import sys
    sys.exit(0)

# 环境变量设置 - 减少启动警告
__version__ = "3.2.7"
