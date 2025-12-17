"""
元数据管理模块 - 增强文件属性追踪
"""
import os
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional
import jieba
import jieba.analyse
from collections import Counter

class MetadataManager:
    """文件元数据管理器"""
    
    def __init__(self, persist_dir: str):
        self.persist_dir = persist_dir
        self.metadata_file = os.path.join(persist_dir, "file_metadata.json")
        self.stats_file = os.path.join(persist_dir, "retrieval_stats.json")
        self.metadata = self._load_metadata()
        self.stats = self._load_stats()
    
    def _load_metadata(self) -> Dict:
        """加载元数据"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _load_stats(self) -> Dict:
        """加载检索统计"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_metadata(self):
        """保存元数据"""
        os.makedirs(self.persist_dir, exist_ok=True)
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
    
    def _save_stats(self):
        """保存统计数据"""
        os.makedirs(self.persist_dir, exist_ok=True)
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        """计算文件哈希值"""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return ""
    
    @staticmethod
    def extract_keywords(text: str, top_k: int = 5) -> List[str]:
        """提取关键词"""
        try:
            keywords = jieba.analyse.extract_tags(text, topK=top_k, withWeight=False)
            return keywords
        except:
            return []
    
    @staticmethod
    def detect_language(text: str) -> str:
        """检测语言"""
        if not text:
            return "unknown"
        
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        english_chars = len([c for c in text if c.isalpha() and ord(c) < 128])
        total_chars = chinese_chars + english_chars
        
        if total_chars == 0:
            return "unknown"
        
        chinese_ratio = chinese_chars / total_chars
        if chinese_ratio > 0.3:
            return "zh" if chinese_ratio > 0.7 else "zh-en"
        return "en"
    
    @staticmethod
    def auto_categorize(filename: str, text: str = "") -> str:
        """自动分类文档"""
        filename_lower = filename.lower()
        text_lower = text.lower()[:500]  # 只看前500字
        
        # 基于文件名和内容的关键词匹配
        categories = {
            "需求文档": ["需求", "requirement", "评审", "确认单"],
            "设计文档": ["设计", "design", "架构", "architecture"],
            "测试文档": ["测试", "test", "用例", "case"],
            "会议纪要": ["会议", "meeting", "纪要", "minutes"],
            "数据文档": ["数据", "data", "统计", "报表", "excel", ".xlsx", ".csv"],
            "代码文档": ["代码", "code", ".py", ".java", ".js"],
            "配置文档": ["配置", "config", "设置", "setting"],
        }
        
        for category, keywords in categories.items():
            if any(kw in filename_lower or kw in text_lower for kw in keywords):
                return category
        
        return "其他文档"
    
    def add_file_metadata(self, file_path: str, doc_ids: List[str], text_sample: str = "") -> Dict:
        """添加文件元数据"""
        filename = os.path.basename(file_path)
        
        # 计算哈希
        file_hash = self.compute_file_hash(file_path)
        
        # 提取关键词
        keywords = self.extract_keywords(text_sample) if text_sample else []
        
        # 检测语言
        language = self.detect_language(text_sample) if text_sample else "unknown"
        
        # 自动分类
        category = self.auto_categorize(filename, text_sample)
        
        # 生成简短摘要（前100字）
        summary = text_sample[:100].strip() if text_sample else ""
        
        metadata = {
            "file_hash": file_hash,
            "keywords": keywords,
            "language": language,
            "category": category,
            "summary": summary,
            "doc_ids": doc_ids,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        
        self.metadata[filename] = metadata
        self._save_metadata()
        
        return metadata
    
    def find_duplicates(self) -> Dict[str, List[str]]:
        """查找重复文件"""
        hash_map = {}
        for filename, meta in self.metadata.items():
            file_hash = meta.get("file_hash", "")
            if file_hash:
                if file_hash not in hash_map:
                    hash_map[file_hash] = []
                hash_map[file_hash].append(filename)
        
        # 只返回有重复的
        return {h: files for h, files in hash_map.items() if len(files) > 1}
    
    def record_retrieval(self, filename: str, score: float):
        """记录检索命中"""
        if filename not in self.stats:
            self.stats[filename] = {
                "hit_count": 0,
                "total_score": 0.0,
                "avg_score": 0.0,
                "last_accessed": None,
                "first_accessed": None
            }
        
        stat = self.stats[filename]
        stat["hit_count"] += 1
        stat["total_score"] += score
        stat["avg_score"] = stat["total_score"] / stat["hit_count"]
        stat["last_accessed"] = datetime.now().isoformat()
        
        if not stat["first_accessed"]:
            stat["first_accessed"] = stat["last_accessed"]
        
        self._save_stats()
    
    def get_file_stats(self, filename: str) -> Dict:
        """获取文件统计信息"""
        return self.stats.get(filename, {
            "hit_count": 0,
            "avg_score": 0.0,
            "last_accessed": None
        })
    
    def get_hot_files(self, top_k: int = 10) -> List[tuple]:
        """获取热门文件"""
        items = [(f, s["hit_count"]) for f, s in self.stats.items()]
        items.sort(key=lambda x: x[1], reverse=True)
        return items[:top_k]
    
    def get_cold_files(self, days: int = 30) -> List[str]:
        """获取冷门文件（N天未访问）"""
        from datetime import timedelta
        threshold = datetime.now() - timedelta(days=days)
        
        cold_files = []
        for filename in self.metadata.keys():
            stat = self.stats.get(filename)
            if not stat or not stat.get("last_accessed"):
                cold_files.append(filename)
            else:
                last_access = datetime.fromisoformat(stat["last_accessed"])
                if last_access < threshold:
                    cold_files.append(filename)
        
        return cold_files
    
    def get_metadata(self, filename: str) -> Optional[Dict]:
        """获取文件元数据"""
        return self.metadata.get(filename)
    
    def update_metadata(self, filename: str, updates: Dict):
        """更新元数据"""
        if filename in self.metadata:
            self.metadata[filename].update(updates)
            self.metadata[filename]["updated_at"] = datetime.now().isoformat()
            self._save_metadata()
    
    def get_all_categories(self) -> Dict[str, int]:
        """获取所有分类统计"""
        categories = Counter()
        for meta in self.metadata.values():
            category = meta.get("category", "其他文档")
            categories[category] += 1
        return dict(categories)
    
    def get_all_keywords(self, top_k: int = 20) -> List[tuple]:
        """获取所有关键词统计"""
        keywords = Counter()
        for meta in self.metadata.values():
            for kw in meta.get("keywords", []):
                keywords[kw] += 1
        return keywords.most_common(top_k)
