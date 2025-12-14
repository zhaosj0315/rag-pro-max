"""
内存泄漏检测和修复工具
解决长时间运行内存增长问题
"""

import gc
import psutil
import threading
import time
import weakref
from datetime import datetime
import streamlit as st

class MemoryLeakDetector:
    def __init__(self):
        self.process = psutil.Process()
        self.baseline_memory = self.get_memory_usage()
        self.memory_history = []
        self.object_refs = weakref.WeakSet()
        self.monitoring = False
        self.monitor_thread = None
        
    def get_memory_usage(self):
        """获取当前内存使用量(MB)"""
        return self.process.memory_info().rss / 1024 / 1024
    
    def start_monitoring(self, interval=30):
        """开始内存监控"""
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop, 
                args=(interval,), 
                daemon=True
            )
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """停止内存监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
    
    def _monitor_loop(self, interval):
        """监控循环"""
        while self.monitoring:
            current_memory = self.get_memory_usage()
            self.memory_history.append({
                'timestamp': datetime.now(),
                'memory_mb': current_memory,
                'growth': current_memory - self.baseline_memory
            })
            
            # 保持历史记录在合理范围内
            if len(self.memory_history) > 100:
                self.memory_history = self.memory_history[-50:]
            
            # 检测内存泄漏
            if self.detect_leak():
                self.auto_cleanup()
            
            time.sleep(interval)
    
    def detect_leak(self, threshold_mb=500, growth_rate=1.5):
        """检测内存泄漏"""
        if len(self.memory_history) < 5:
            return False
        
        current = self.memory_history[-1]
        
        # 检查绝对内存使用量
        if current['memory_mb'] > threshold_mb:
            return True
        
        # 检查内存增长率
        if len(self.memory_history) >= 10:
            recent_growth = current['memory_mb'] - self.memory_history[-10]['memory_mb']
            if recent_growth > growth_rate * 10:  # 10个周期内增长超过阈值
                return True
        
        return False
    
    def auto_cleanup(self):
        """自动内存清理"""
        print(f"🧹 检测到内存泄漏，开始自动清理...")
        
        # 1. 清理Streamlit缓存
        if hasattr(st, 'cache_data'):
            st.cache_data.clear()
        if hasattr(st, 'cache_resource'):
            st.cache_resource.clear()
        
        # 2. 清理会话状态中的大对象
        self._cleanup_session_state()
        
        # 3. 清理GPU缓存
        self._cleanup_gpu_cache()
        
        # 4. 强制垃圾回收
        collected = gc.collect()
        
        # 5. 更新基线
        new_memory = self.get_memory_usage()
        freed_mb = self.memory_history[-1]['memory_mb'] - new_memory
        
        print(f"✅ 内存清理完成: 释放 {freed_mb:.1f}MB, 回收 {collected} 个对象")
        
        # 记录清理事件
        self.memory_history.append({
            'timestamp': datetime.now(),
            'memory_mb': new_memory,
            'growth': new_memory - self.baseline_memory,
            'cleanup': True,
            'freed_mb': freed_mb
        })
    
    def _cleanup_session_state(self):
        """清理会话状态"""
        if not hasattr(st, 'session_state'):
            return
        
        # 清理大型对象
        large_keys = []
        for key, value in st.session_state.items():
            try:
                # 估算对象大小
                if hasattr(value, '__sizeof__'):
                    size = value.__sizeof__()
                    if size > 10 * 1024 * 1024:  # 大于10MB
                        large_keys.append(key)
            except:
                pass
        
        # 清理历史记录（保留最近50条）
        if 'messages' in st.session_state and len(st.session_state.messages) > 50:
            st.session_state.messages = st.session_state.messages[-50:]
        
        if 'suggestions_history' in st.session_state and len(st.session_state.suggestions_history) > 20:
            st.session_state.suggestions_history = st.session_state.suggestions_history[-20:]
    
    def _cleanup_gpu_cache(self):
        """清理GPU缓存"""
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                torch.mps.empty_cache()
        except ImportError:
            pass
    
    def get_memory_report(self):
        """获取内存报告"""
        if not self.memory_history:
            return "暂无内存监控数据"
        
        current = self.memory_history[-1]
        max_memory = max(h['memory_mb'] for h in self.memory_history)
        min_memory = min(h['memory_mb'] for h in self.memory_history)
        
        report = f"""
📊 内存使用报告:
- 当前内存: {current['memory_mb']:.1f} MB
- 基线内存: {self.baseline_memory:.1f} MB
- 内存增长: {current['growth']:.1f} MB
- 最高内存: {max_memory:.1f} MB
- 最低内存: {min_memory:.1f} MB
- 监控周期: {len(self.memory_history)} 次
"""
        
        # 统计清理次数
        cleanup_count = sum(1 for h in self.memory_history if h.get('cleanup', False))
        if cleanup_count > 0:
            report += f"- 自动清理: {cleanup_count} 次\n"
        
        return report
    
    def register_object(self, obj):
        """注册需要监控的对象"""
        self.object_refs.add(obj)
    
    def get_object_count(self):
        """获取监控对象数量"""
        return len(self.object_refs)

# 全局内存泄漏检测器
memory_detector = MemoryLeakDetector()
