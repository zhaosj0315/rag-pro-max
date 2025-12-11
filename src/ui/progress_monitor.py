"""
实时进度监控器
提供OCR处理和文档上传的实时进度显示
"""

import time
import streamlit as st
from typing import Dict, Optional
from dataclasses import dataclass
from threading import Lock

@dataclass
class ProgressInfo:
    """进度信息"""
    task_id: str
    task_name: str
    total_items: int
    completed_items: int
    current_item: str
    start_time: float
    status: str  # 'running', 'completed', 'failed', 'paused'
    error_message: Optional[str] = None

class ProgressMonitor:
    """实时进度监控器"""
    
    def __init__(self):
        self.tasks: Dict[str, ProgressInfo] = {}
        self.lock = Lock()
    
    def start_task(self, task_id: str, task_name: str, total_items: int):
        """开始新任务"""
        with self.lock:
            self.tasks[task_id] = ProgressInfo(
                task_id=task_id,
                task_name=task_name,
                total_items=total_items,
                completed_items=0,
                current_item="准备中...",
                start_time=time.time(),
                status="running"
            )
    
    def update_progress(self, task_id: str, completed: int, current_item: str = ""):
        """更新任务进度"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].completed_items = completed
                if current_item:
                    self.tasks[task_id].current_item = current_item
    
    def complete_task(self, task_id: str):
        """完成任务"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].status = "completed"
                self.tasks[task_id].completed_items = self.tasks[task_id].total_items
    
    def fail_task(self, task_id: str, error_message: str):
        """任务失败"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].status = "failed"
                self.tasks[task_id].error_message = error_message
    
    def pause_task(self, task_id: str):
        """暂停任务"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].status = "paused"
    
    def resume_task(self, task_id: str):
        """恢复任务"""
        with self.lock:
            if task_id in self.tasks:
                self.tasks[task_id].status = "running"
    
    def get_task_info(self, task_id: str) -> Optional[ProgressInfo]:
        """获取任务信息"""
        with self.lock:
            return self.tasks.get(task_id)
    
    def render_progress(self, task_id: str, container=None):
        """渲染进度显示"""
        task_info = self.get_task_info(task_id)
        if not task_info:
            return
        
        if container is None:
            container = st
        
        # 计算进度
        progress = task_info.completed_items / task_info.total_items if task_info.total_items > 0 else 0
        
        # 计算耗时和预估时间
        elapsed_time = time.time() - task_info.start_time
        if progress > 0:
            estimated_total = elapsed_time / progress
            remaining_time = estimated_total - elapsed_time
        else:
            remaining_time = 0
        
        # 状态图标
        status_icons = {
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "paused": "⏸️"
        }
        
        # 显示进度条
        with container.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"{status_icons.get(task_info.status, '🔄')} **{task_info.task_name}**")
                
                # 进度条
                progress_bar = st.progress(progress)
                
                # 详细信息
                info_text = f"进度: {task_info.completed_items}/{task_info.total_items} "
                info_text += f"({progress:.1%}) | "
                info_text += f"耗时: {elapsed_time:.1f}秒"
                
                if task_info.status == "running" and remaining_time > 0:
                    info_text += f" | 预计剩余: {remaining_time:.1f}秒"
                
                st.caption(info_text)
                
                # 当前处理项
                if task_info.current_item and task_info.status == "running":
                    st.caption(f"正在处理: {task_info.current_item}")
                
                # 错误信息
                if task_info.status == "failed" and task_info.error_message:
                    st.error(f"错误: {task_info.error_message}")
            
            with col2:
                # 控制按钮
                if task_info.status == "running":
                    if st.button("⏸️ 暂停", key=f"pause_{task_id}"):
                        self.pause_task(task_id)
                        st.rerun()
                elif task_info.status == "paused":
                    if st.button("▶️ 继续", key=f"resume_{task_id}"):
                        self.resume_task(task_id)
                        st.rerun()
    
    def render_all_tasks(self):
        """渲染所有活跃任务"""
        active_tasks = [
            task for task in self.tasks.values() 
            if task.status in ["running", "paused"]
        ]
        
        if not active_tasks:
            return
        
        st.subheader("📊 处理进度")
        
        for task in active_tasks:
            self.render_progress(task.task_id)
            st.divider()
    
    def cleanup_completed_tasks(self, max_age: int = 300):
        """清理已完成的旧任务"""
        current_time = time.time()
        with self.lock:
            to_remove = []
            for task_id, task in self.tasks.items():
                if (task.status in ["completed", "failed"] and 
                    current_time - task.start_time > max_age):
                    to_remove.append(task_id)
            
            for task_id in to_remove:
                del self.tasks[task_id]

# 全局实例
progress_monitor = ProgressMonitor()
