"""
可配置的行业网站管理服务
支持用户自定义每个行业的网站列表
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from pathlib import Path

class ConfigurableIndustryService:
    """可配置的行业网站服务"""
    
    def __init__(self):
        self.config_file = Path("config/custom_industry_sites.json")
        self.config_data = self._load_config()
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {"custom_industries": {}}
        except Exception as e:
            print(f"加载配置失败: {e}")
            return {"custom_industries": {}}
    
    def _save_config(self):
        """保存配置文件"""
        try:
            os.makedirs(self.config_file.parent, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get_all_industries(self) -> List[str]:
        """获取所有行业列表"""
        return list(self.config_data.get("custom_industries", {}).keys())
    
    def get_industry_sites(self, industry: str) -> List[Dict]:
        """获取指定行业的网站列表"""
        industry_data = self.config_data.get("custom_industries", {}).get(industry, {})
        sites = industry_data.get("sites", [])
        # 按优先级排序
        return sorted(sites, key=lambda x: x.get("priority", 999))
    
    def add_site(self, industry: str, name: str, url: str, priority: int = 999, difficulty: int = 2):
        """为指定行业添加网站"""
        if "custom_industries" not in self.config_data:
            self.config_data["custom_industries"] = {}
        
        if industry not in self.config_data["custom_industries"]:
            self.config_data["custom_industries"][industry] = {
                "name": industry,
                "description": "",
                "keywords": [],
                "sites": []
            }
        
        new_site = {
            "name": name,
            "url": url,
            "priority": priority,
            "difficulty": difficulty
        }
        
        self.config_data["custom_industries"][industry]["sites"].append(new_site)
        self._save_config()
    
    def remove_site(self, industry: str, site_index: int):
        """删除指定行业的网站"""
        if industry in self.config_data.get("custom_industries", {}):
            sites = self.config_data["custom_industries"][industry]["sites"]
            if 0 <= site_index < len(sites):
                sites.pop(site_index)
                self._save_config()
    
    def update_site(self, industry: str, site_index: int, name: str, url: str, priority: int = None):
        """更新指定网站信息"""
        if industry in self.config_data.get("custom_industries", {}):
            sites = self.config_data["custom_industries"][industry]["sites"]
            if 0 <= site_index < len(sites):
                sites[site_index]["name"] = name
                sites[site_index]["url"] = url
                if priority is not None:
                    sites[site_index]["priority"] = priority
                self._save_config()
    
    def add_industry(self, industry_name: str, description: str = "", keywords: List[str] = None):
        """添加新行业"""
        if "custom_industries" not in self.config_data:
            self.config_data["custom_industries"] = {}
        
        self.config_data["custom_industries"][industry_name] = {
            "name": industry_name,
            "description": description,
            "keywords": keywords or [],
            "sites": []
        }
        self._save_config()
    
    def remove_industry(self, industry: str):
        """删除行业"""
        if industry in self.config_data.get("custom_industries", {}):
            del self.config_data["custom_industries"][industry]
            self._save_config()
    
    def recommend_sites_for_keyword(self, keyword: str) -> List[str]:
        """根据关键词智能推荐网站"""
        keyword_lower = keyword.lower()
        matched_sites = []
        
        # 遍历所有行业，找到匹配的关键词
        for industry_data in self.config_data.get("custom_industries", {}).values():
            keywords = industry_data.get("keywords", [])
            
            # 检查关键词匹配
            if any(kw.lower() in keyword_lower for kw in keywords):
                sites = industry_data.get("sites", [])
                # 按优先级排序，取前5个
                top_sites = sorted(sites, key=lambda x: x.get("priority", 999))[:5]
                matched_sites.extend([site["name"] for site in top_sites])
        
        # 如果没有匹配，返回默认推荐
        if not matched_sites:
            return ["维基百科", "百度百科", "知乎"]
        
        return matched_sites[:10]  # 最多返回10个
    
    def get_sites_for_crawling(self, industry: str) -> Tuple[List[str], List[str]]:
        """获取用于爬取的网站URL和名称列表"""
        sites = self.get_industry_sites(industry)
        urls = [site["url"] for site in sites]
        names = [site["name"] for site in sites]
        return urls, names

# 全局实例
_configurable_service = None

def get_configurable_industry_service() -> ConfigurableIndustryService:
    """获取可配置行业服务实例"""
    global _configurable_service
    if _configurable_service is None:
        _configurable_service = ConfigurableIndustryService()
    return _configurable_service
