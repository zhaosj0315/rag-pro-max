"""
实时进度追踪器
可视化显示文件处理进度
"""

import streamlit as st
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable
import json
import os

class ProgressTracker:
    def __init__(self):
        self.active_tasks = {}
        self.completed_tasks = []
        self.task_counter = 0
        self.lock = threading.Lock()
        
    def create_task(self, name: str, total_items: int, description: str = "") -> str:
        """创建新任务"""
        with self.lock:
            task_id = f"task_{self.task_counter}_{int(time.time())}"
            self.task_counter += 1
            
            self.active_tasks[task_id] = {
                'id': task_id,
                'name': name,
                'description': description,
                'total_items': total_items,
                'completed_items': 0,
                'start_time': datetime.now(),
                'status': 'running',
                'current_item': '',
                'error_count': 0,
                'warnings': []
            }
            
            return task_id
    
    def update_progress(self, task_id: str, completed: int, current_item: str = "", 
                       status: str = "running", error: str = None):
        """更新任务进度"""
        with self.lock:
            if task_id not in self.active_tasks:
                return
            
            task = self.active_tasks[task_id]
            task['completed_items'] = completed
            task['current_item'] = current_item
            task['status'] = status
            
            if error:
                task['error_count'] += 1
                task['warnings'].append({
                    'timestamp': datetime.now().isoformat(),
                    'message': error
                })
    
    def complete_task(self, task_id: str, success: bool = True, final_message: str = ""):
        """完成任务"""
        with self.lock:
            if task_id not in self.active_tasks:
                return
            
            task = self.active_tasks[task_id]
            task['end_time'] = datetime.now()
            task['status'] = 'completed' if success else 'failed'
            task['final_message'] = final_message
            task['duration'] = (task['end_time'] - task['start_time']).total_seconds()
            
            # 移动到已完成任务
            self.completed_tasks.append(task)
            del self.active_tasks[task_id]
            
            # 保持最近50个已完成任务
            if len(self.completed_tasks) > 50:
                self.completed_tasks = self.completed_tasks[-50:]
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        with self.lock:
            if task_id in self.active_tasks:
                return self.active_tasks[task_id].copy()
            
            for task in self.completed_tasks:
                if task['id'] == task_id:
                    return task.copy()
            
            return None
    
    def get_all_active_tasks(self) -> List[Dict]:
        """获取所有活跃任务"""
        with self.lock:
            return list(self.active_tasks.values())
    
    def get_recent_completed_tasks(self, limit: int = 10) -> List[Dict]:
        """获取最近完成的任务"""
        with self.lock:
            return self.completed_tasks[-limit:]
    
    def render_progress_panel(self):
        """渲染进度面板"""
        st.header("📊 实时处理进度")
        
        # 活跃任务
        active_tasks = self.get_all_active_tasks()
        if active_tasks:
            st.subheader("🔄 正在处理")
            
            for task in active_tasks:
                self._render_task_progress(task)
        else:
            st.info("📝 当前没有正在处理的任务")
        
        # 最近完成的任务
        completed_tasks = self.get_recent_completed_tasks(5)
        if completed_tasks:
            st.subheader("✅ 最近完成")
            
            for task in reversed(completed_tasks):
                self._render_completed_task(task)
    
    def _render_task_progress(self, task: Dict):
        """渲染单个任务进度"""
        with st.container():
            # 任务标题和状态
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**{task['name']}**")
                if task['description']:
                    st.caption(task['description'])
            
            with col2:
                status_icon = {
                    'running': '🔄',
                    'paused': '⏸️',
                    'error': '❌'
                }.get(task['status'], '🔄')
                st.write(f"{status_icon} {task['status'].title()}")
            
            with col3:
                progress_percent = (task['completed_items'] / max(task['total_items'], 1)) * 100
                st.metric("进度", f"{progress_percent:.1f}%")
            
            # 进度条
            progress_bar = st.progress(task['completed_items'] / max(task['total_items'], 1))
            
            # 详细信息
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.caption(f"已完成: {task['completed_items']}/{task['total_items']}")
            
            with col2:
                elapsed = (datetime.now() - task['start_time']).total_seconds()
                st.caption(f"耗时: {elapsed:.1f}秒")
            
            with col3:
                if task['error_count'] > 0:
                    st.caption(f"⚠️ 错误: {task['error_count']}")
            
            # 当前处理项
            if task['current_item']:
                st.caption(f"正在处理: {task['current_item']}")
            
            # 警告信息
            if task['warnings']:
                with st.expander(f"⚠️ 警告信息 ({len(task['warnings'])})"):
                    for warning in task['warnings'][-3:]:  # 显示最近3个警告
                        st.warning(f"{warning['timestamp']}: {warning['message']}")
            
            st.divider()
    
    def _render_completed_task(self, task: Dict):
        """渲染已完成任务"""
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**{task['name']}**")
            
            with col2:
                status_icon = '✅' if task['status'] == 'completed' else '❌'
                st.write(f"{status_icon} {task['status'].title()}")
            
            with col3:
                st.caption(f"{task['completed_items']}/{task['total_items']}")
            
            with col4:
                duration = task.get('duration', 0)
                st.caption(f"{duration:.1f}秒")
            
            if task.get('final_message'):
                st.caption(task['final_message'])
            
            st.divider()
    
    def render_task_controls(self, task_id: str):
        """渲染任务控制按钮"""
        task = self.get_task_status(task_id)
        if not task or task['status'] != 'running':
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⏸️ 暂停", key=f"pause_{task_id}"):
                self.update_progress(task_id, task['completed_items'], 
                                   task['current_item'], 'paused')
                st.rerun()
        
        with col2:
            if st.button("▶️ 继续", key=f"resume_{task_id}"):
                self.update_progress(task_id, task['completed_items'], 
                                   task['current_item'], 'running')
                st.rerun()
        
        with col3:
            if st.button("❌ 停止", key=f"stop_{task_id}"):
                self.complete_task(task_id, False, "用户手动停止")
                st.rerun()

# 全局进度追踪器实例
_progress_tracker = None

def get_progress_tracker() -> ProgressTracker:
    """获取进度追踪器实例"""
    global _progress_tracker
    if _progress_tracker is None:
        _progress_tracker = ProgressTracker()
    return _progress_tracker

def render_progress_panel():
    """渲染进度面板的入口函数"""
    tracker = get_progress_tracker()
    tracker.render_progress_panel()
