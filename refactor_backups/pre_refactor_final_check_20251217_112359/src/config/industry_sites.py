"""
各行各业高质量网站配置
扩展关键词搜索功能到全行业覆盖
"""

# 各行各业网站配置
INDUSTRY_SITES = {
    # 🏥 医疗健康类
    "healthcare": [
        {
            "name": "丁香园",
            "url": "https://www.dxy.com/",
            "difficulty": 3,
            "description": "专业医疗资讯平台，医生和医学生首选"
        },
        {
            "name": "好大夫在线",
            "url": "https://www.haodf.com/",
            "difficulty": 3,
            "description": "医疗咨询和健康科普平台"
        },
        {
            "name": "春雨医生",
            "url": "https://www.chunyuyisheng.com/",
            "difficulty": 3,
            "description": "在线医疗咨询和健康管理"
        }
    ],
    
    # 💰 金融财经类
    "finance": [
        {
            "name": "东方财富网",
            "url": "https://www.eastmoney.com/",
            "difficulty": 2,
            "description": "综合财经资讯和股票信息"
        },
        {
            "name": "雪球",
            "url": "https://xueqiu.com/",
            "difficulty": 3,
            "description": "投资者社区和财经资讯"
        },
        {
            "name": "金融界",
            "url": "https://www.jrj.com/",
            "difficulty": 2,
            "description": "专业金融资讯和分析"
        },
        {
            "name": "中国人民银行",
            "url": "http://www.pbc.gov.cn/",
            "difficulty": 2,
            "description": "央行官方政策和金融法规"
        }
    ],
    
    # 🎓 教育培训类
    "education": [
        {
            "name": "中国大学MOOC",
            "url": "https://www.icourse163.org/",
            "difficulty": 2,
            "description": "高质量在线课程平台"
        },
        {
            "name": "学堂在线",
            "url": "https://www.xuetangx.com/",
            "difficulty": 2,
            "description": "清华大学发起的MOOC平台"
        },
        {
            "name": "网易公开课",
            "url": "https://open.163.com/",
            "difficulty": 2,
            "description": "免费的高质量教育资源"
        },
        {
            "name": "中国教育在线",
            "url": "https://www.eol.cn/",
            "difficulty": 2,
            "description": "教育资讯和政策解读"
        }
    ],
    
    # ⚖️ 法律法规类
    "legal": [
        {
            "name": "中国政府网",
            "url": "http://www.gov.cn/",
            "difficulty": 2,
            "description": "官方政策法规发布平台"
        },
        {
            "name": "法律图书馆",
            "url": "http://www.law-lib.com/",
            "difficulty": 2,
            "description": "法律法规数据库"
        },
        {
            "name": "找法网",
            "url": "https://www.findlaw.cn/",
            "difficulty": 3,
            "description": "法律咨询和案例分析"
        },
        {
            "name": "华律网",
            "url": "https://www.66law.cn/",
            "difficulty": 3,
            "description": "法律服务和知识普及"
        }
    ],
    
    # 🏭 制造业类
    "manufacturing": [
        {
            "name": "机械工程师",
            "url": "https://www.cmiw.cn/",
            "difficulty": 3,
            "description": "机械制造技术资讯"
        },
        {
            "name": "中国制造网",
            "url": "https://cn.made-in-china.com/",
            "difficulty": 2,
            "description": "制造业B2B平台和资讯"
        },
        {
            "name": "工控网",
            "url": "https://www.gongkong.com/",
            "difficulty": 2,
            "description": "工业自动化技术资讯"
        }
    ],
    
    # 🛒 电商零售类
    "ecommerce": [
        {
            "name": "亿邦动力",
            "url": "https://www.ebrun.com/",
            "difficulty": 2,
            "description": "电商行业资讯和分析"
        },
        {
            "name": "派代网",
            "url": "https://www.paidai.com/",
            "difficulty": 3,
            "description": "电商运营和营销知识"
        },
        {
            "name": "中国电子商务研究中心",
            "url": "http://www.100ec.cn/",
            "difficulty": 2,
            "description": "电商行业研究和报告"
        }
    ],
    
    # 🎬 媒体娱乐类
    "media": [
        {
            "name": "新浪娱乐",
            "url": "https://ent.sina.com.cn/",
            "difficulty": 2,
            "description": "娱乐资讯和明星动态"
        },
        {
            "name": "豆瓣",
            "url": "https://www.douban.com/",
            "difficulty": 3,
            "description": "影视书籍评论和文化内容"
        },
        {
            "name": "虎嗅网",
            "url": "https://www.huxiu.com/",
            "difficulty": 3,
            "description": "科技和商业媒体资讯"
        }
    ],
    
    # 🏠 房地产类
    "realestate": [
        {
            "name": "房天下",
            "url": "https://www.fang.com/",
            "difficulty": 2,
            "description": "房地产资讯和市场分析"
        },
        {
            "name": "安居客",
            "url": "https://www.anjuke.com/",
            "difficulty": 3,
            "description": "房产信息和购房指南"
        },
        {
            "name": "搜房网",
            "url": "https://www.soufun.com/",
            "difficulty": 2,
            "description": "房地产门户和资讯"
        }
    ],
    
    # 🚗 汽车行业类
    "automotive": [
        {
            "name": "汽车之家",
            "url": "https://www.autohome.com.cn/",
            "difficulty": 2,
            "description": "汽车资讯、评测和购车指南"
        },
        {
            "name": "易车网",
            "url": "https://www.yiche.com/",
            "difficulty": 2,
            "description": "汽车媒体和服务平台"
        },
        {
            "name": "太平洋汽车网",
            "url": "https://www.pcauto.com.cn/",
            "difficulty": 2,
            "description": "专业汽车资讯和测评"
        }
    ],
    
    # 🍔 餐饮美食类
    "food": [
        {
            "name": "美食天下",
            "url": "https://www.meishichina.com/",
            "difficulty": 2,
            "description": "菜谱大全和美食制作"
        },
        {
            "name": "下厨房",
            "url": "https://www.xiachufang.com/",
            "difficulty": 3,
            "description": "美食社区和菜谱分享"
        },
        {
            "name": "红餐网",
            "url": "https://www.hongcan.com/",
            "difficulty": 2,
            "description": "餐饮行业资讯和经营管理"
        }
    ]
}

def get_industry_sites(industry):
    """根据行业获取网站列表"""
    return INDUSTRY_SITES.get(industry, [])

def get_all_industries():
    """获取所有支持的行业列表"""
    return list(INDUSTRY_SITES.keys())

def get_industry_description():
    """获取行业描述"""
    descriptions = {
        "programming": "🔧 技术开发 - 编程语言、开发工具、云服务技术",
        "healthcare": "🏥 医疗健康 - 医疗资讯、健康科普、医学知识",
        "finance": "💰 金融财经 - 股票投资、财经资讯、金融政策",
        "education": "🎓 教育培训 - 在线课程、教育资讯、学习资源",
        "legal": "⚖️ 法律法规 - 政策法规、法律咨询、案例分析",
        "manufacturing": "🏭 制造业 - 工业技术、制造工艺、自动化",
        "ecommerce": "🛒 电商零售 - 电商运营、零售趋势、营销策略",
        "media": "🎬 媒体娱乐 - 影视资讯、文化内容、科技媒体",
        "realestate": "🏠 房地产 - 房产资讯、市场分析、购房指南",
        "automotive": "🚗 汽车行业 - 汽车资讯、评测导购、行业动态",
        "food": "🍔 餐饮美食 - 菜谱大全、美食制作、餐饮经营"
    }
    return descriptions

def get_recommended_sites_by_industry(industry, max_difficulty=3):
    """根据行业获取推荐网站（按难度筛选）"""
    sites = get_industry_sites(industry)
    return [site for site in sites if site["difficulty"] <= max_difficulty]

# 全行业默认推荐网站（每个行业选1-2个最容易爬取的）
ALL_INDUSTRY_SITES = [
    # 技术开发（原有）
    "https://www.runoob.com/",
    "https://docs.python.org/zh-cn/3/",
    "https://help.aliyun.com/",
    
    # 各行各业扩展
    "https://www.eastmoney.com/",  # 金融
    "https://www.icourse163.org/",  # 教育
    "http://www.gov.cn/",  # 法律
    "https://cn.made-in-china.com/",  # 制造
    "https://www.ebrun.com/",  # 电商
    "https://www.autohome.com.cn/",  # 汽车
    "https://www.meishichina.com/"  # 美食
]

ALL_INDUSTRY_NAMES = [
    "菜鸟教程", "Python文档", "阿里云",
    "东方财富", "中国大学MOOC", "中国政府网",
    "中国制造网", "亿邦动力", "汽车之家", "美食天下"
]
