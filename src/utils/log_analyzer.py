from src.app_logging.log_manager import LogManager

logger = LogManager()

"""
日志分析器 - 解析和统计处理日志
"""

import re
from collections import defaultdict

class LogAnalyzer:
    def __init__(self):
        self.ocr_stats = {
            'total_files': 0,
            'success_count': 0,
            'failed_count': 0,
            'total_pages': 0,
            'total_time': 0,
            'avg_speed': 0,
            'files': []
        }
        
        self.vector_stats = {
            'total_nodes': 0,
            'processed_batches': 0,
            'total_time': 0,
            'avg_speed': 0,
            'progress': 0
        }
        
        self.timeline = []
    
    def parse_log_text(self, log_text):
        """解析日志文本"""
        lines = log_text.strip().split('\n')
        
        for line in lines:
            self._parse_ocr_line(line)
            self._parse_vector_line(line)
            self._parse_timeline_line(line)
    
    def _parse_ocr_line(self, line):
        """解析OCR相关日志"""
        # OCR处理开始
        if "使用优化OCR处理器处理" in line:
            match = re.search(r'处理 (\d+) 页', line)
            if match:
                pages = int(match.group(1))
                self.ocr_stats['total_files'] += 1
                self.ocr_stats['total_pages'] += pages
        
        # OCR处理完成
        elif "OCR处理完成:" in line:
            match = re.search(r'(\d+\.?\d*)秒, (\d+\.?\d*)页/秒', line)
            if match:
                time_cost = float(match.group(1))
                speed = float(match.group(2))
                self.ocr_stats['total_time'] += time_cost
                
                # 检查是否成功
                if "⚠️  OCR未提取到文本内容" in line:
                    self.ocr_stats['failed_count'] += 1
                else:
                    self.ocr_stats['success_count'] += 1
    
    def _parse_vector_line(self, line):
        """解析向量化相关日志"""
        # 解析节点数量
        if "解析文档片段" in line:
            match = re.search(r'共 (\d+) 个', line)
            if match:
                self.vector_stats['total_nodes'] = int(match.group(1))
        
        # 解析向量化进度
        elif "Generating embeddings:" in line:
            match = re.search(r'(\d+)%.*?(\d+)/(\d+)', line)
            if match:
                progress = int(match.group(1))
                current = int(match.group(2))
                total = int(match.group(3))
                self.vector_stats['progress'] = progress
                self.vector_stats['processed_batches'] += 1
    
    def _parse_timeline_line(self, line):
        """解析时间线"""
        # 提取时间戳
        time_match = re.search(r'\[(\d{2}:\d{2}:\d{2})\]', line)
        if time_match:
            timestamp = time_match.group(1)
            
            # 提取步骤信息
            step_match = re.search(r'步骤 (\d+)/(\d+)', line)
            if step_match:
                current_step = int(step_match.group(1))
                total_steps = int(step_match.group(2))
                
                self.timeline.append({
                    'time': timestamp,
                    'step': current_step,
                    'total_steps': total_steps,
                    'description': line.split(']', 2)[-1].strip() if ']' in line else line
                })
    
    def generate_summary(self):
        """生成处理摘要"""
        # 计算OCR统计
        if self.ocr_stats['total_time'] > 0:
            self.ocr_stats['avg_speed'] = self.ocr_stats['total_pages'] / self.ocr_stats['total_time']
        
        success_rate = 0
        if self.ocr_stats['total_files'] > 0:
            success_rate = (self.ocr_stats['success_count'] / self.ocr_stats['total_files']) * 100
        
        summary = {
            'ocr_summary': {
                '📄 总文件数': self.ocr_stats['total_files'],
                '📑 总页数': self.ocr_stats['total_pages'],
                '✅ 成功文件': self.ocr_stats['success_count'],
                '❌ 失败文件': self.ocr_stats['failed_count'],
                '📊 成功率': f"{success_rate:.1f}%",
                '⏱️ 总耗时': f"{self.ocr_stats['total_time']:.1f}秒",
                '🚀 平均速度': f"{self.ocr_stats['avg_speed']:.1f}页/秒"
            },
            'vector_summary': {
                '📝 文档片段': self.vector_stats['total_nodes'],
                '📦 处理批次': self.vector_stats['processed_batches'],
                '📈 当前进度': f"{self.vector_stats['progress']}%"
            },
            'timeline': self.timeline
        }
        
        return summary
    
    def print_summary(self):
        """打印格式化摘要"""
        summary = self.generate_summary()
        
        logger.info("=" * 60)
        logger.info("📊 处理摘要报告")
        logger.info("=" * 60)
        
        logger.info("\n🔍 OCR处理统计:")
        for key, value in summary['ocr_summary'].items():
            logger.info(f"   {key}: {value}")
        
        logger.info("\n🧠 向量化统计:")
        for key, value in summary['vector_summary'].items():
            logger.info(f"   {key}: {value}")
        
        if summary['timeline']:
            logger.info("\n⏰ 处理时间线:")
            for event in summary['timeline']:
                logger.info(f"   [{event['time']}] 步骤{event['step']}/{event['total_steps']}: {event['description']}")
        
        logger.info("=" * 60)

def analyze_current_log():
    """分析当前日志"""
    log_text = """
🔍 检测到扫描版PDF，启用增强OCR处理...
📊 使用优化OCR处理器处理 4 页
✅ OCR处理完成: 3.1秒, 1.3页/秒
⚠️  OCR未提取到文本内容
📊 使用优化OCR处理器处理 122 页
✅ OCR处理完成: 307.3秒, 2.8页/秒
⚠️  OCR未提取到文本内容
📊 使用优化OCR处理器处理 39 页
✅ OCR处理完成: 205.7秒, 2.8页/秒
⚠️  OCR未提取到文本内容
📊 使用优化OCR处理器处理 1 页
✅ OCR处理完成: 2.0秒, 0.5页/秒
⚠️  OCR未提取到文本内容
📊 使用优化OCR处理器处理 221 页
✅ OCR处理完成: 205.7秒, 2.8页/秒
⚠️  OCR未提取到文本内容
📊 使用优化OCR处理器处理 6 页
✅ OCR处理完成: 3.1秒, 1.9页/秒
⚠️  OCR未提取到文本内容
📊 使用优化OCR处理器处理 417 页
✅ OCR处理完成: 560.5秒, 2.9页/秒
⚠️  OCR未提取到文本内容
📊 使用优化OCR处理器处理 225 页
✅ OCR处理完成: 330.2秒, 2.9页/秒
⚠️  OCR未提取到文本内容
📊 使用优化OCR处理器处理 90 页
✅ OCR处理完成: 43.3秒, 2.8页/秒
⚠️  OCR未提取到文本内容
ℹ️ [06:39:40] 📂 [步骤 4/6] 构建文件清单
ℹ️ [06:39:40] 📂 [步骤 5/6] 解析文档片段 (共 27940 个)
ℹ️ [06:39:53] 📂 [步骤 6/6] 向量化和索引构建
Generating embeddings: 100%|##########| 2048/2048 [01:32<00:00, 22.17it/s]
Generating embeddings: 44%|####3     | 900/2048 [00:41<00:51, 22.34it/s]
"""
    
    analyzer = LogAnalyzer()
    analyzer.parse_log_text(log_text)
    analyzer.print_summary()

if __name__ == "__main__":
    analyze_current_log()
