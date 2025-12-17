"""
Top20 高质量文档网站配置
用于关键词搜索功能的网站列表
"""

# Top20 推荐网站配置
TOP20_SITES = {
    # 编程开发类 (1-5)
    "programming": [
        {
            "name": "菜鸟教程",
            "url": "https://www.runoob.com/",
            "difficulty": 2,  # 1-5, 数字越小越容易爬取
            "description": "中文编程教程大全，覆盖50+语言和技术"
        },
        {
            "name": "Python官方文档",
            "url": "https://docs.python.org/zh-cn/3/",
            "difficulty": 2,
            "description": "Python权威文档，中文版完整"
        },
        {
            "name": "MDN Web文档",
            "url": "https://developer.mozilla.org/zh-CN/",
            "difficulty": 3,
            "description": "Web开发权威资料，HTML/CSS/JS全覆盖"
        },
        {
            "name": "Node.js文档",
            "url": "https://nodejs.org/docs/",
            "difficulty": 2,
            "description": "服务端JavaScript开发文档"
        },
        {
            "name": "React文档",
            "url": "https://reactjs.org/docs/",
            "difficulty": 3,
            "description": "前端框架文档，现代Web开发必备"
        }
    ],
    
    # 云服务/DevOps类 (6-10)
    "cloud_devops": [
        {
            "name": "阿里云帮助",
            "url": "https://help.aliyun.com/",
            "difficulty": 2,
            "description": "云计算服务文档，中文友好 (已验证)"
        },
        {
            "name": "Docker文档",
            "url": "https://docs.docker.com/",
            "difficulty": 2,
            "description": "容器化技术权威文档"
        },
        {
            "name": "腾讯云文档",
            "url": "https://cloud.tencent.com/document",
            "difficulty": 3,
            "description": "腾讯云服务文档，结构清晰"
        },
        {
            "name": "Kubernetes文档",
            "url": "https://kubernetes.io/docs/",
            "difficulty": 3,
            "description": "容器编排平台文档"
        },
        {
            "name": "GitLab CI/CD",
            "url": "https://docs.gitlab.com/ee/ci/",
            "difficulty": 3,
            "description": "持续集成/持续部署文档"
        }
    ],
    
    # 工具框架类 (11-15)
    "tools_frameworks": [
        {
            "name": "Vue.js文档",
            "url": "https://vuejs.org/guide/",
            "difficulty": 2,
            "description": "渐进式JavaScript框架"
        },
        {
            "name": "Git文档",
            "url": "https://git-scm.com/docs",
            "difficulty": 2,
            "description": "版本控制系统文档"
        },
        {
            "name": "Spring官方指南",
            "url": "https://spring.io/guides",
            "difficulty": 3,
            "description": "Java企业级开发框架"
        },
        {
            "name": "Django文档",
            "url": "https://docs.djangoproject.com/",
            "difficulty": 3,
            "description": "Python Web框架文档"
        },
        {
            "name": "VS Code文档",
            "url": "https://code.visualstudio.com/docs",
            "difficulty": 3,
            "description": "代码编辑器使用文档"
        }
    ],
    
    # 学习教程类 (16-20)
    "tutorials": [
        {
            "name": "W3Schools",
            "url": "https://www.w3schools.com/",
            "difficulty": 2,
            "description": "Web技术在线教程，英文版"
        },
        {
            "name": "廖雪峰教程",
            "url": "https://www.liaoxuefeng.com/",
            "difficulty": 3,
            "description": "中文编程教程，质量很高"
        },
        {
            "name": "GitHub文档",
            "url": "https://docs.github.com/",
            "difficulty": 3,
            "description": "代码托管平台使用文档"
        },
        {
            "name": "Microsoft文档",
            "url": "https://docs.microsoft.com/zh-cn/",
            "difficulty": 3,
            "description": "微软技术文档中心"
        },
        {
            "name": "Stack Overflow文档",
            "url": "https://stackoverflow.com/documentation",
            "difficulty": 4,
            "description": "程序员问答社区文档 (有反爬)"
        }
    ]
}

def get_easy_sites(max_difficulty=2):
    """获取容易爬取的网站列表"""
    easy_sites = []
    for category in TOP20_SITES.values():
        for site in category:
            if site["difficulty"] <= max_difficulty:
                easy_sites.append(site)
    return easy_sites

def get_sites_by_category(category):
    """根据分类获取网站列表"""
    return TOP20_SITES.get(category, [])

def get_all_sites():
    """获取所有网站列表"""
    all_sites = []
    for category in TOP20_SITES.values():
        all_sites.extend(category)
    return all_sites

def get_recommended_sites():
    """获取推荐的网站列表 (难度<=3)"""
    recommended = []
    for category in TOP20_SITES.values():
        for site in category:
            if site["difficulty"] <= 3:
                recommended.append(site)
    return recommended

# 默认使用的网站列表 (最容易爬取的10个)
DEFAULT_SEARCH_SITES = [
    "https://www.runoob.com/",  # 菜鸟教程
    "https://docs.python.org/zh-cn/3/",  # Python文档
    "https://help.aliyun.com/",  # 阿里云 (已验证)
    "https://docs.docker.com/",  # Docker文档
    "https://nodejs.org/docs/",  # Node.js文档
    "https://vuejs.org/guide/",  # Vue.js文档
    "https://git-scm.com/docs",  # Git文档
    "https://www.w3schools.com/",  # W3Schools
    "https://cloud.tencent.com/document",  # 腾讯云文档
    "https://developer.mozilla.org/zh-CN/"  # MDN文档
]

DEFAULT_SITE_NAMES = [
    "菜鸟教程", "Python文档", "阿里云", "Docker文档", "Node.js文档",
    "Vue.js文档", "Git文档", "W3Schools", "腾讯云", "MDN文档"
]
