"""
统一网站配置管理
整合所有行业的高质量网站配置
"""

# 统一的行业网站配置
UNIFIED_INDUSTRY_SITES = {
    # 🔧 技术开发类 (最完善)
    "programming": {
        "name": "🔧 技术开发",
        "description": "编程语言、开发工具、云服务技术",
        "sites": [
            {"name": "菜鸟教程", "url": "https://www.runoob.com/", "difficulty": 2},
            {"name": "Python官方文档", "url": "https://docs.python.org/zh-cn/3/", "difficulty": 2},
            {"name": "阿里云帮助", "url": "https://help.aliyun.com/", "difficulty": 2},
            {"name": "Docker文档", "url": "https://docs.docker.com/", "difficulty": 2},
            {"name": "Node.js文档", "url": "https://nodejs.org/docs/", "difficulty": 2},
            {"name": "Vue.js文档", "url": "https://vuejs.org/guide/", "difficulty": 2},
            {"name": "Git文档", "url": "https://git-scm.com/docs", "difficulty": 2},
            {"name": "MDN文档", "url": "https://developer.mozilla.org/zh-CN/", "difficulty": 3},
            {"name": "腾讯云文档", "url": "https://cloud.tencent.com/document", "difficulty": 3},
            {"name": "W3Schools", "url": "https://www.w3schools.com/", "difficulty": 2}
        ]
    },
    
    # 🏥 医疗健康类
    "healthcare": {
        "name": "🏥 医疗健康",
        "description": "医疗资讯、健康科普、医学知识",
        "sites": [
            {"name": "丁香园", "url": "https://www.dxy.com/", "difficulty": 3},
            {"name": "好大夫在线", "url": "https://www.haodf.com/", "difficulty": 3},
            {"name": "春雨医生", "url": "https://www.chunyuyisheng.com/", "difficulty": 3}
        ]
    },
    
    # 💰 金融财经类
    "finance": {
        "name": "💰 金融财经",
        "description": "股票投资、财经资讯、金融政策",
        "sites": [
            {"name": "东方财富网", "url": "https://www.eastmoney.com/", "difficulty": 2},
            {"name": "雪球", "url": "https://xueqiu.com/", "difficulty": 3},
            {"name": "金融界", "url": "https://www.jrj.com/", "difficulty": 2},
            {"name": "中国人民银行", "url": "http://www.pbc.gov.cn/", "difficulty": 2}
        ]
    },
    
    # 🎓 教育培训类
    "education": {
        "name": "🎓 教育培训",
        "description": "在线课程、教育资讯、学习资源",
        "sites": [
            {"name": "中国大学MOOC", "url": "https://www.icourse163.org/", "difficulty": 2},
            {"name": "学堂在线", "url": "https://www.xuetangx.com/", "difficulty": 2},
            {"name": "网易公开课", "url": "https://open.163.com/", "difficulty": 2},
            {"name": "中国教育在线", "url": "https://www.eol.cn/", "difficulty": 2}
        ]
    },
    
    # ⚖️ 法律法规类
    "legal": {
        "name": "⚖️ 法律法规",
        "description": "政策法规、法律咨询、案例分析",
        "sites": [
            {"name": "中国政府网", "url": "http://www.gov.cn/", "difficulty": 2},
            {"name": "法律图书馆", "url": "http://www.law-lib.com/", "difficulty": 2},
            {"name": "找法网", "url": "https://www.findlaw.cn/", "difficulty": 3},
            {"name": "华律网", "url": "https://www.66law.cn/", "difficulty": 3}
        ]
    },
    
    # 🏭 制造业类
    "manufacturing": {
        "name": "🏭 制造业",
        "description": "工业技术、制造工艺、自动化",
        "sites": [
            {"name": "中国制造网", "url": "https://cn.made-in-china.com/", "difficulty": 2},
            {"name": "工控网", "url": "https://www.gongkong.com/", "difficulty": 2},
            {"name": "机械工程师", "url": "https://www.cmiw.cn/", "difficulty": 3}
        ]
    },
    
    # 🛒 电商零售类
    "ecommerce": {
        "name": "🛒 电商零售",
        "description": "电商运营、零售趋势、营销策略",
        "sites": [
            {"name": "亿邦动力", "url": "https://www.ebrun.com/", "difficulty": 2},
            {"name": "派代网", "url": "https://www.paidai.com/", "difficulty": 3},
            {"name": "中国电子商务研究中心", "url": "http://www.100ec.cn/", "difficulty": 2}
        ]
    },
    
    # 🎬 媒体娱乐类
    "media": {
        "name": "🎬 媒体娱乐",
        "description": "影视资讯、文化内容、科技媒体",
        "sites": [
            {"name": "豆瓣", "url": "https://www.douban.com/", "difficulty": 3},
            {"name": "虎嗅网", "url": "https://www.huxiu.com/", "difficulty": 3},
            {"name": "新浪娱乐", "url": "https://ent.sina.com.cn/", "difficulty": 2}
        ]
    },
    
    # 🏠 房地产类
    "realestate": {
        "name": "🏠 房地产",
        "description": "房产资讯、市场分析、购房指南",
        "sites": [
            {"name": "房天下", "url": "https://www.fang.com/", "difficulty": 2},
            {"name": "安居客", "url": "https://www.anjuke.com/", "difficulty": 3},
            {"name": "搜房网", "url": "https://www.soufun.com/", "difficulty": 2}
        ]
    },
    
    # 🚗 汽车行业类
    "automotive": {
        "name": "🚗 汽车行业",
        "description": "汽车资讯、评测导购、行业动态",
        "sites": [
            {"name": "汽车之家", "url": "https://www.autohome.com.cn/", "difficulty": 2},
            {"name": "易车网", "url": "https://www.yiche.com/", "difficulty": 2},
            {"name": "太平洋汽车网", "url": "https://www.pcauto.com.cn/", "difficulty": 2}
        ]
    },
    
    # 🍔 餐饮美食类
    "food": {
        "name": "🍔 餐饮美食",
        "description": "菜谱大全、美食制作、餐饮经营",
        "sites": [
            {"name": "美食天下", "url": "https://www.meishichina.com/", "difficulty": 2},
            {"name": "下厨房", "url": "https://www.xiachufang.com/", "difficulty": 3},
            {"name": "红餐网", "url": "https://www.hongcan.com/", "difficulty": 2}
        ]
    }
}

def get_industry_list():
    """获取所有行业的显示列表"""
    return [f"{config['name']} - {config['description']}" 
            for config in UNIFIED_INDUSTRY_SITES.values()]

def get_industry_sites(industry_display_name):
    """根据显示名称获取行业网站"""
    for key, config in UNIFIED_INDUSTRY_SITES.items():
        if config['name'] in industry_display_name:
            return [site['url'] for site in config['sites']], [site['name'] for site in config['sites']]
    
    # 默认返回技术开发
    programming_sites = UNIFIED_INDUSTRY_SITES['programming']['sites']
    return [site['url'] for site in programming_sites], [site['name'] for site in programming_sites]

def get_easy_sites(industry_key, max_difficulty=2):
    """获取指定行业中容易爬取的网站"""
    if industry_key not in UNIFIED_INDUSTRY_SITES:
        industry_key = 'programming'
    
    sites = UNIFIED_INDUSTRY_SITES[industry_key]['sites']
    easy_sites = [site for site in sites if site['difficulty'] <= max_difficulty]
    return [site['url'] for site in easy_sites], [site['name'] for site in easy_sites]

# 向后兼容的默认配置
DEFAULT_SEARCH_SITES = [site['url'] for site in UNIFIED_INDUSTRY_SITES['programming']['sites']]
DEFAULT_SITE_NAMES = [site['name'] for site in UNIFIED_INDUSTRY_SITES['programming']['sites']]
