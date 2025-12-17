"""
爬取统计管理器
实现实时监控、效果分析和可视化展示
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict, deque
import os

class CrawlStatsManager:
    """爬取统计管理器"""
    
    def __init__(self, stats_file: str = "app_logs/crawl_stats.json"):
        self.stats_file = stats_file
        self.current_session = {
            'session_id': None,
            'start_time': None,
            'end_time': None,
            'industry': None,
            'keywords': [],
            'total_urls': 0,
            'successful_urls': 0,
            'failed_urls': 0,
            'total_content_length': 0,
            'avg_quality_score': 0,
            'avg_relevance_score': 0,
            'processing_time': 0,
            'crawl_speed': 0,  # 页面/分钟
            'error_details': [],
            'site_stats': {},  # 各网站统计
            'quality_distribution': {'high': 0, 'medium': 0, 'low': 0}
        }
        self.historical_stats = self._load_historical_stats()
        self.real_time_metrics = deque(maxlen=100)  # 实时指标队列
        
    def _load_historical_stats(self) -> List[Dict]:
        """加载历史统计数据"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载历史统计失败: {e}")
        return []
    
    def _save_stats(self):
        """保存统计数据"""
        try:
            os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.historical_stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存统计失败: {e}")
    
    def start_session(self, industry: str, keywords: List[str], total_urls: int):
        """开始新的爬取会话"""
        session_id = f"{industry}_{int(time.time())}"
        self.current_session = {
            'session_id': session_id,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'industry': industry,
            'keywords': keywords,
            'total_urls': total_urls,
            'successful_urls': 0,
            'failed_urls': 0,
            'total_content_length': 0,
            'avg_quality_score': 0,
            'avg_relevance_score': 0,
            'processing_time': 0,
            'crawl_speed': 0,
            'error_details': [],
            'site_stats': {},
            'quality_distribution': {'high': 0, 'medium': 0, 'low': 0}
        }
        
        # 添加实时指标
        self.real_time_metrics.append({
            'timestamp': time.time(),
            'event': 'session_start',
            'industry': industry,
            'total_urls': total_urls
        })
        
        return session_id
    
    def update_progress(self, successful: int, failed: int, 
                       current_url: str = None, site_name: str = None):
        """更新爬取进度"""
        self.current_session['successful_urls'] = successful
        self.current_session['failed_urls'] = failed
        
        # 更新网站统计
        if site_name:
            if site_name not in self.current_session['site_stats']:
                self.current_session['site_stats'][site_name] = {
                    'successful': 0,
                    'failed': 0,
                    'total_content': 0,
                    'avg_quality': 0
                }
        
        # 计算实时指标
        total_processed = successful + failed
        if self.current_session['total_urls'] > 0:
            progress = total_processed / self.current_session['total_urls']
        else:
            progress = 0
        
        # 计算爬取速度
        if self.current_session['start_time']:
            start_time = datetime.fromisoformat(self.current_session['start_time'])
            elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60
            if elapsed_minutes > 0:
                self.current_session['crawl_speed'] = successful / elapsed_minutes
        
        # 添加实时指标
        self.real_time_metrics.append({
            'timestamp': time.time(),
            'event': 'progress_update',
            'successful': successful,
            'failed': failed,
            'progress': progress,
            'crawl_speed': self.current_session['crawl_speed'],
            'current_url': current_url
        })
    
    def add_content_result(self, url: str, site_name: str, success: bool,
                          content_length: int = 0, quality_score: float = 0,
                          relevance_score: float = 0, error: str = None):
        """添加内容处理结果"""
        # 更新网站统计
        if site_name not in self.current_session['site_stats']:
            self.current_session['site_stats'][site_name] = {
                'successful': 0,
                'failed': 0,
                'total_content': 0,
                'avg_quality': 0,
                'quality_scores': []
            }
        
        site_stats = self.current_session['site_stats'][site_name]
        
        if success:
            site_stats['successful'] += 1
            site_stats['total_content'] += content_length
            site_stats['quality_scores'].append(quality_score)
            
            # 更新平均质量评分
            if site_stats['quality_scores']:
                site_stats['avg_quality'] = sum(site_stats['quality_scores']) / len(site_stats['quality_scores'])
            
            # 更新总体统计
            self.current_session['total_content_length'] += content_length
            
            # 质量分布统计
            if quality_score >= 70:
                self.current_session['quality_distribution']['high'] += 1
            elif quality_score >= 40:
                self.current_session['quality_distribution']['medium'] += 1
            else:
                self.current_session['quality_distribution']['low'] += 1
                
        else:
            site_stats['failed'] += 1
            if error:
                self.current_session['error_details'].append({
                    'url': url,
                    'site': site_name,
                    'error': error,
                    'timestamp': datetime.now().isoformat()
                })
        
        # 添加实时指标
        self.real_time_metrics.append({
            'timestamp': time.time(),
            'event': 'content_processed',
            'url': url,
            'site': site_name,
            'success': success,
            'quality_score': quality_score,
            'relevance_score': relevance_score
        })
    
    def end_session(self):
        """结束爬取会话"""
        self.current_session['end_time'] = datetime.now().isoformat()
        
        # 计算处理时间
        if self.current_session['start_time']:
            start_time = datetime.fromisoformat(self.current_session['start_time'])
            end_time = datetime.fromisoformat(self.current_session['end_time'])
            self.current_session['processing_time'] = (end_time - start_time).total_seconds()
        
        # 计算平均质量和相关性评分
        all_quality_scores = []
        all_relevance_scores = []
        
        for site_stats in self.current_session['site_stats'].values():
            if 'quality_scores' in site_stats:
                all_quality_scores.extend(site_stats['quality_scores'])
        
        if all_quality_scores:
            self.current_session['avg_quality_score'] = sum(all_quality_scores) / len(all_quality_scores)
        
        # 保存到历史记录
        self.historical_stats.append(self.current_session.copy())
        self._save_stats()
        
        # 添加实时指标
        self.real_time_metrics.append({
            'timestamp': time.time(),
            'event': 'session_end',
            'session_id': self.current_session['session_id'],
            'total_time': self.current_session['processing_time'],
            'success_rate': self.get_current_success_rate()
        })
    
    def get_current_stats(self) -> Dict:
        """获取当前会话统计"""
        stats = self.current_session.copy()
        
        # 计算成功率
        total_processed = stats['successful_urls'] + stats['failed_urls']
        if total_processed > 0:
            stats['success_rate'] = stats['successful_urls'] / total_processed
        else:
            stats['success_rate'] = 0
        
        # 计算进度
        if stats['total_urls'] > 0:
            stats['progress'] = total_processed / stats['total_urls']
        else:
            stats['progress'] = 0
        
        return stats
    
    def get_current_success_rate(self) -> float:
        """获取当前成功率"""
        total = self.current_session['successful_urls'] + self.current_session['failed_urls']
        if total > 0:
            return self.current_session['successful_urls'] / total
        return 0
    
    def get_industry_comparison(self) -> Dict:
        """获取各行业效果对比"""
        industry_stats = defaultdict(list)
        
        # 按行业分组统计
        for session in self.historical_stats:
            industry = session.get('industry', 'unknown')
            if session.get('successful_urls', 0) > 0:  # 只统计有成功数据的会话
                industry_stats[industry].append({
                    'success_rate': session['successful_urls'] / max(session['successful_urls'] + session['failed_urls'], 1),
                    'avg_quality': session.get('avg_quality_score', 0),
                    'crawl_speed': session.get('crawl_speed', 0),
                    'content_length': session.get('total_content_length', 0)
                })
        
        # 计算各行业平均指标
        comparison = {}
        for industry, sessions in industry_stats.items():
            if sessions:
                comparison[industry] = {
                    'session_count': len(sessions),
                    'avg_success_rate': sum(s['success_rate'] for s in sessions) / len(sessions),
                    'avg_quality_score': sum(s['avg_quality'] for s in sessions) / len(sessions),
                    'avg_crawl_speed': sum(s['crawl_speed'] for s in sessions) / len(sessions),
                    'avg_content_length': sum(s['content_length'] for s in sessions) / len(sessions)
                }
        
        return comparison
    
    def get_recent_trends(self, days: int = 7) -> Dict:
        """获取最近趋势数据"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_sessions = []
        
        for session in self.historical_stats:
            if session.get('start_time'):
                session_date = datetime.fromisoformat(session['start_time'])
                if session_date >= cutoff_date:
                    recent_sessions.append(session)
        
        if not recent_sessions:
            return {'message': f'最近{days}天无爬取记录'}
        
        # 按日期分组
        daily_stats = defaultdict(list)
        for session in recent_sessions:
            date_str = session['start_time'][:10]  # YYYY-MM-DD
            daily_stats[date_str].append(session)
        
        # 计算每日趋势
        trends = {}
        for date, sessions in daily_stats.items():
            total_success = sum(s['successful_urls'] for s in sessions)
            total_failed = sum(s['failed_urls'] for s in sessions)
            total_processed = total_success + total_failed
            
            trends[date] = {
                'session_count': len(sessions),
                'total_processed': total_processed,
                'success_rate': total_success / max(total_processed, 1),
                'avg_quality': sum(s.get('avg_quality_score', 0) for s in sessions) / len(sessions),
                'total_content': sum(s.get('total_content_length', 0) for s in sessions)
            }
        
        return trends
    
    def get_real_time_metrics(self, last_n: int = 20) -> List[Dict]:
        """获取实时指标"""
        return list(self.real_time_metrics)[-last_n:]
    
    def get_site_performance_ranking(self) -> List[Dict]:
        """获取网站性能排名"""
        site_performance = defaultdict(lambda: {
            'total_sessions': 0,
            'total_successful': 0,
            'total_failed': 0,
            'quality_scores': [],
            'content_lengths': []
        })
        
        # 收集所有网站数据
        for session in self.historical_stats:
            for site_name, site_stats in session.get('site_stats', {}).items():
                perf = site_performance[site_name]
                perf['total_sessions'] += 1
                perf['total_successful'] += site_stats.get('successful', 0)
                perf['total_failed'] += site_stats.get('failed', 0)
                
                if 'quality_scores' in site_stats:
                    perf['quality_scores'].extend(site_stats['quality_scores'])
                
                perf['content_lengths'].append(site_stats.get('total_content', 0))
        
        # 计算排名指标
        rankings = []
        for site_name, perf in site_performance.items():
            total_requests = perf['total_successful'] + perf['total_failed']
            if total_requests > 0:
                success_rate = perf['total_successful'] / total_requests
                avg_quality = sum(perf['quality_scores']) / len(perf['quality_scores']) if perf['quality_scores'] else 0
                avg_content = sum(perf['content_lengths']) / len(perf['content_lengths']) if perf['content_lengths'] else 0
                
                # 综合评分 (成功率40% + 质量30% + 内容量30%)
                composite_score = (success_rate * 0.4 + (avg_quality/100) * 0.3 + 
                                 min(avg_content/1000, 1) * 0.3) * 100
                
                rankings.append({
                    'site_name': site_name,
                    'success_rate': success_rate,
                    'avg_quality_score': avg_quality,
                    'avg_content_length': avg_content,
                    'total_sessions': perf['total_sessions'],
                    'total_requests': total_requests,
                    'composite_score': composite_score
                })
        
        # 按综合评分排序
        return sorted(rankings, key=lambda x: x['composite_score'], reverse=True)

# 使用示例
if __name__ == "__main__":
    stats_manager = CrawlStatsManager()
    
    # 模拟爬取会话
    session_id = stats_manager.start_session("技术开发", ["Python", "编程"], 10)
    
    # 模拟进度更新
    stats_manager.update_progress(3, 1, "https://example.com", "测试网站")
    
    # 模拟内容结果
    stats_manager.add_content_result(
        "https://example.com/page1", 
        "测试网站", 
        True, 
        content_length=1500, 
        quality_score=75.5,
        relevance_score=0.8
    )
    
    # 结束会话
    stats_manager.end_session()
    
    # 获取统计信息
    current_stats = stats_manager.get_current_stats()
    print("当前统计:", json.dumps(current_stats, indent=2, ensure_ascii=False))
    
    industry_comparison = stats_manager.get_industry_comparison()
    print("行业对比:", json.dumps(industry_comparison, indent=2, ensure_ascii=False))
