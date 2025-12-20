"""
智能爬取优化器 - v2.4.1
自动分析网站类型并推荐最佳爬取参数
"""

import re
from urllib.parse import urlparse
from typing import Dict, Tuple, List
import requests
from bs4 import BeautifulSoup

class CrawlOptimizer:
    """智能爬取优化器"""
    
    def __init__(self):
        # 网站类型配置 - 调整为更现实的参数
        self.site_configs = {
            "documentation": {
                "depth": 2,
                "pages_per_level": 5,  # 降低每层页数
                "description": "技术文档网站，内容层次深",
                "examples": ["docs.python.org", "developer.mozilla.org"]
            },
            "news": {
                "depth": 2,
                "pages_per_level": 5,  # 降低每层页数
                "description": "新闻网站，文章数量多",
                "examples": ["36kr.com", "techcrunch.com"]
            },
            "ecommerce": {
                "depth": 2,
                "pages_per_level": 5,  # 降低每层页数
                "description": "电商网站，商品页面丰富",
                "examples": ["jd.com", "taobao.com"]
            },
            "blog": {
                "depth": 2,
                "pages_per_level": 5,  # 降低每层页数
                "description": "博客网站，文章分类清晰",
                "examples": ["medium.com", "dev.to"]
            },
            "forum": {
                "depth": 2,
                "pages_per_level": 5,  # 降低每层页数
                "description": "论坛网站，讨论层次深",
                "examples": ["stackoverflow.com", "reddit.com"]
            },
            "corporate": {
                "depth": 2,
                "pages_per_level": 5,  # 大幅降低企业官网预估
                "description": "企业官网，结构相对简单",
                "examples": ["apple.com", "microsoft.com"]
            },
            "wiki": {
                "depth": 3,
                "pages_per_level": 30,  # 降低每层页数
                "description": "百科网站，内容丰富互联",
                "examples": ["wikipedia.org", "baike.baidu.com"]
            }
        }
        
        # 网站类型识别规则
        self.type_patterns = {
            "documentation": [
                r"docs?\.", r"developer\.", r"api\.", r"reference\.",
                r"guide", r"tutorial", r"manual"
            ],
            "news": [
                r"news", r"tech", r"36kr", r"techcrunch", r"ithome",
                r"cnbeta", r"pingwest"
            ],
            "ecommerce": [
                r"shop", r"store", r"mall", r"buy", r"jd\.com",
                r"taobao", r"tmall", r"amazon"
            ],
            "blog": [
                r"blog", r"medium", r"dev\.to", r"csdn", r"jianshu"
            ],
            "forum": [
                r"forum", r"bbs", r"discuss", r"stackoverflow",
                r"reddit", r"zhihu"
            ],
            "wiki": [
                r"wiki", r"baike", r"encyclopedia"
            ]
        }
    
    def analyze_website(self, url: str) -> Dict:
        """分析网站并返回推荐配置"""
        try:
            # 解析URL
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            path = parsed.path.lower()
            
            # 识别网站类型
            site_type = self._identify_site_type(domain, path)
            
            # 获取推荐配置
            config = self.site_configs.get(site_type, self.site_configs["corporate"])
            
            # 尝试获取网站信息
            site_info = self._get_site_info(url)
            
            # 修正预估逻辑 - 更现实的预估
            realistic_estimate = self._calculate_realistic_estimate(
                config["depth"], 
                config["pages_per_level"], 
                site_type,
                site_info
            )
            
            return {
                "site_type": site_type,
                "recommended_depth": config["depth"],
                "recommended_pages": config["pages_per_level"],
                "description": config["description"],
                "estimated_pages": realistic_estimate,
                "confidence": site_info.get("confidence", 0.7),
                "site_info": site_info
            }
            
        except Exception as e:
            # 默认配置
            return {
                "site_type": "unknown",
                "recommended_depth": 2,
                "recommended_pages": 20,
                "description": "未知网站类型，使用默认配置",
                "estimated_pages": 40,  # 更现实的默认预估
                "confidence": 0.5,
                "error": str(e)
            }
    
    def _calculate_realistic_estimate(self, depth: int, pages_per_level: int, 
                                    site_type: str, site_info: Dict) -> int:
        """计算更现实的页面预估"""
        
        # 基础预估：线性增长而非指数增长
        base_estimate = pages_per_level * depth
        
        # 根据网站类型调整系数
        type_multipliers = {
            "documentation": 2.5,  # 文档网站链接较多
            "news": 3.0,          # 新闻网站文章丰富
            "ecommerce": 4.0,     # 电商网站商品页面多
            "blog": 1.8,          # 博客相对较少
            "forum": 3.5,         # 论坛讨论多
            "corporate": 1.2,     # 企业官网页面有限
            "wiki": 2.8           # 百科内容丰富
        }
        
        multiplier = type_multipliers.get(site_type, 1.5)
        
        # 根据实际链接数量调整
        total_links = site_info.get("total_links", 50)
        if total_links > 100:
            multiplier *= 1.5
        elif total_links < 20:
            multiplier *= 0.6
        
        # 计算现实预估
        realistic_estimate = int(base_estimate * multiplier)
        
        # 设置合理上下限
        min_estimate = max(depth * 5, 10)  # 最少每层5页
        max_estimate = pages_per_level * depth * 10  # 最多10倍
        
        return max(min_estimate, min(realistic_estimate, max_estimate))
    
    def _identify_site_type(self, domain: str, path: str) -> str:
        """识别网站类型"""
        full_url = domain + path
        
        for site_type, patterns in self.type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, full_url, re.IGNORECASE):
                    return site_type
        
        return "corporate"  # 默认类型
    
    def _get_site_info(self, url: str, timeout: int = 5) -> Dict:
        """获取网站基本信息"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=timeout)
            if response.status_code != 200:
                return {"confidence": 0.5}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 分析页面结构
            nav_links = len(soup.find_all(['nav', 'menu']))
            total_links = len(soup.find_all('a', href=True))
            
            # 计算置信度
            confidence = min(0.9, 0.5 + (total_links / 100) * 0.4)
            
            return {
                "title": soup.title.string if soup.title else "Unknown",
                "nav_sections": nav_links,
                "total_links": total_links,
                "confidence": confidence
            }
            
        except Exception:
            return {"confidence": 0.5}
    
    def get_popular_sites(self) -> Dict[str, List[Dict]]:
        """获取热门网站预设"""
        popular_sites = {
            "技术文档": [
                {"name": "Python官方文档", "url": "https://docs.python.org/", "type": "documentation"},
                {"name": "MDN Web文档", "url": "https://developer.mozilla.org/", "type": "documentation"},
                {"name": "React文档", "url": "https://react.dev/", "type": "documentation"},
            ],
            "新闻资讯": [
                {"name": "36氪", "url": "https://36kr.com/", "type": "news"},
                {"name": "TechCrunch", "url": "https://techcrunch.com/", "type": "news"},
                {"name": "IT之家", "url": "https://www.ithome.com/", "type": "news"},
            ],
            "技术博客": [
                {"name": "Medium", "url": "https://medium.com/", "type": "blog"},
                {"name": "Dev.to", "url": "https://dev.to/", "type": "blog"},
                {"name": "CSDN", "url": "https://blog.csdn.net/", "type": "blog"},
            ],
            "问答论坛": [
                {"name": "Stack Overflow", "url": "https://stackoverflow.com/", "type": "forum"},
                {"name": "知乎", "url": "https://www.zhihu.com/", "type": "forum"},
                {"name": "Reddit", "url": "https://www.reddit.com/", "type": "forum"},
            ]
        }
        
        return popular_sites
    
    def generate_crawl_report(self, results: Dict) -> str:
        """生成爬取报告"""
        report = f"""
📊 **爬取分析报告**

🌐 **网站类型**: {results['site_type']}
📝 **描述**: {results['description']}
🎯 **推荐深度**: {results['recommended_depth']}层
📄 **每层页数**: {results['recommended_pages']}页
📈 **预估总页数**: {results['estimated_pages']:,}页
🔍 **置信度**: {results['confidence']:.1%}

💡 **优化建议**:
- 根据网站结构自动调整参数
- 建议使用推荐配置以获得最佳效果
- 大型网站建议分批爬取
        """
        
        return report.strip()

# 使用示例
if __name__ == "__main__":
    optimizer = CrawlOptimizer()
    
    # 测试网站分析
    test_urls = [
        "https://docs.python.org/",
        "https://36kr.com/",
        "https://stackoverflow.com/"
    ]
    
    for url in test_urls:
        print(f"\n🔍 分析网站: {url}")
        result = optimizer.analyze_website(url)
        print(optimizer.generate_crawl_report(result))
