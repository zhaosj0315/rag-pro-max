"""
Core模块 - 多进程安全版本
"""

# 延迟导入，避免多进程问题
def get_state_manager():
    """获取状态管理器"""
    from .state_manager import state
    return state

def get_main_controller():
    """获取主控制器"""
    from .main_controller import MainController
    return MainController

# 兼容性导出
try:
    from .state_manager import StateManager, state
except ImportError:
    # 多进程环境中的fallback
    class StateManager:
        def __init__(self):
            self._state = {}
        def get(self, key, default=None):
            return self._state.get(key, default)
        def set(self, key, value):
            self._state[key] = value
    
    state = StateManager()
