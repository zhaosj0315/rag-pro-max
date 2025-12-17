"""
进度日志记录器
提供详细的步骤耗时、进度百分比和ETA估算
"""

import time
import sys
from datetime import datetime
from typing import Optional

class ProgressLogger:
    def __init__(self, total_steps: int = 6, logger=None):
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = time.time()
        self.step_start_time = 0
        self.logger = logger

    def start_step(self, step_num: int, description: str):
        """开始一个新步骤"""
        self.current_step = step_num
        self.step_start_time = time.time()
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        msg = f"📂 [步骤 {step_num}/{self.total_steps}] {description}"
        if self.logger:
            self.logger.info(msg)
        else:
            print(f"ℹ️ [{timestamp}] {msg}")

    def update_progress(self, current: int, total: int, prefix: str = ""):
        """更新当前步骤的进度"""
        if total == 0:
            return
            
        percentage = (current / total) * 100
        elapsed = time.time() - self.step_start_time
        
        # 估算剩余时间 (ETA)
        if percentage > 0:
            total_estimated = elapsed / (percentage / 100)
            remaining = total_estimated - elapsed
            eta_str = f"{remaining:.1f}s"
        else:
            eta_str = "计算中..."
            
        msg = f"   ⏳ {prefix}: {current}/{total} ({percentage:.1f}%) - 耗时: {elapsed:.1f}s - 预计剩余: {eta_str}"
        
        # 使用 \r 覆盖当前行 (仅在终端有效)
        sys.stdout.write(f"\r{msg}")
        sys.stdout.flush()

    def end_step(self, summary: str):
        """结束当前步骤"""
        sys.stdout.write("\n") # 换行
        duration = time.time() - self.step_start_time
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        msg = f"   ✅ 完成: {summary} (耗时: {duration:.2f}s)"
        if self.logger:
            self.logger.success(msg)
        else:
            print(f"ℹ️ [{timestamp}] {msg}")

    def finish_all(self, success: bool = True):
        """完成所有任务"""
        total_duration = time.time() - self.start_time
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        status_icon = "🎉" if success else "❌"
        status_text = "全部完成" if success else "处理失败"
        
        msg = f"{status_icon} [{timestamp}] {status_text} - 总耗时: {total_duration:.2f}s"
        if self.logger:
            if success:
                self.logger.success(msg)
            else:
                self.logger.error(msg)
        else:
            print(f"{msg}")

