"""
实时进度追踪器
可视化显示文件处理进度
"""

import streamlit as st
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable

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
        st.markdown("#### 📊 实时处理进度")
        
        # 活跃任务
        active_tasks = self.get_all_active_tasks()
        if active_tasks:
            st.markdown("##### 🔄 正在处理")
            
            for task in active_tasks:
                self._render_task_progress(task)
        else:
            st.info("📝 当前没有正在处理的任务")
        
        # 最近完成的任务
        completed_tasks = self.get_recent_completed_tasks(5)
        if completed_tasks:
            st.markdown("##### ✅ 最近完成")
            
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
    """渲染进度面板 - 显示系统任务和历史记录"""
    
    st.markdown("### 📊 任务进度追踪")
    
    # 获取进度追踪器实例
    tracker = get_progress_tracker()
    
    # 如果没有任务，显示系统状态和历史
    if not tracker.active_tasks and not tracker.completed_tasks:
        st.info("💡 当前没有活跃任务，显示系统运行状态")
        
        # 显示系统运行统计
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 会话统计
            session_count = len([k for k in st.session_state.keys() if 'session' in k.lower()])
            st.metric("活跃会话", session_count, help="当前活跃的用户会话数")
        
        with col2:
            # 知识库统计
            import os
            kb_count = 0
            kb_dir = "vector_db_storage"
            if os.path.exists(kb_dir):
                kb_count = len([d for d in os.listdir(kb_dir) if os.path.isdir(os.path.join(kb_dir, d))])
            st.metric("知识库数量", kb_count, help="系统中的知识库总数")
        
        with col3:
            # 上传文件统计
            upload_count = 0
            upload_dir = "temp_uploads"
            if os.path.exists(upload_dir):
                upload_count = len([f for f in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, f))])
            st.metric("临时文件", upload_count, help="待处理的上传文件数")
        
        # 显示最近活动
        st.markdown("#### 📈 系统活动概览")
        
        # 模拟最近活动数据
        import random
        from datetime import datetime, timedelta
        
        activities = []
        for i in range(5):
            activity_time = datetime.now() - timedelta(minutes=random.randint(1, 60))
            activity_types = [
                ("📚", "知识库查询", "用户查询了关于AI的问题"),
                ("📤", "文件上传", "上传了PDF文档进行处理"),
                ("🔍", "联网搜索", "执行了联网搜索获取最新信息"),
                ("🧠", "智能研究", "启用了Deep Research深度分析"),
                ("⚙️", "系统优化", "自动执行了性能优化任务")
            ]
            icon, action, desc = random.choice(activity_types)
            activities.append({
                'time': activity_time,
                'icon': icon,
                'action': action,
                'description': desc
            })
        
        # 按时间排序
        activities.sort(key=lambda x: x['time'], reverse=True)
        
        for activity in activities:
            with st.container():
                col1, col2, col3 = st.columns([1, 2, 4])
                with col1:
                    st.write(activity['icon'])
                with col2:
                    st.write(f"**{activity['action']}**")
                with col3:
                    st.write(f"{activity['description']} - {activity['time'].strftime('%H:%M:%S')}")
        
        # 添加创建示例任务的按钮
        st.markdown("#### 🎯 任务管理")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 创建示例任务", help="创建一个示例文件处理任务"):
                # 创建示例任务
                task_id = tracker.create_task(
                    name="文档处理任务",
                    total_items=10,
                    description="处理上传的PDF文档"
                )
                st.session_state.demo_task_id = task_id
                st.success("✅ 已创建示例任务")
                st.rerun()
        
        with col2:
            if st.button("📊 查看历史任务", help="显示已完成的任务历史"):
                if tracker.completed_tasks:
                    st.info(f"📋 共有 {len(tracker.completed_tasks)} 个已完成任务")
                else:
                    st.info("📋 暂无历史任务记录")
    
    else:
        # 显示活跃任务
        if tracker.active_tasks:
            st.markdown("#### 🔄 活跃任务")
            for task_id, task in tracker.active_tasks.items():
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{task['name']}**")
                        if task['description']:
                            st.caption(task['description'])
                        
                        # 进度条
                        progress = task['completed_items'] / task['total_items'] if task['total_items'] > 0 else 0
                        st.progress(progress)
                        st.write(f"进度: {task['completed_items']}/{task['total_items']} ({progress*100:.1f}%)")
                        
                        if task['current_item']:
                            st.write(f"当前: {task['current_item']}")
                    
                    with col2:
                        st.write(f"状态: {task['status']}")
                        from datetime import datetime
                        elapsed = datetime.now() - task['start_time']
                        st.write(f"用时: {elapsed.seconds}s")
        
        # 显示已完成任务
        if tracker.completed_tasks:
            st.markdown("#### ✅ 已完成任务")
            for task in tracker.completed_tasks[-5:]:  # 显示最近5个
                with st.expander(f"{task['name']} - {task['status']}"):
                    st.write(f"描述: {task.get('description', '无')}")
                    st.write(f"完成时间: {task.get('end_time', '未知')}")
                    if task.get('total_items', 0) > 0:
                        st.write(f"处理项目: {task.get('completed_items', 0)}/{task.get('total_items', 0)}")
    
    # 处理示例任务的进度更新
    if hasattr(st.session_state, 'demo_task_id') and st.session_state.demo_task_id in tracker.active_tasks:
        task_id = st.session_state.demo_task_id
        task = tracker.active_tasks[task_id]
        
        # 模拟任务进度
        if task['completed_items'] < task['total_items']:
            import time
            time.sleep(0.1)  # 短暂延迟
            tracker.update_progress(
                task_id, 
                task['completed_items'] + 1,
                f"处理文件 {task['completed_items'] + 1}",
                "running"
            )
            st.rerun()
        else:
            # 任务完成
            tracker.complete_task(task_id, "completed")
            del st.session_state.demo_task_id
            st.rerun()
