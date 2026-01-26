
import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

# 将项目根目录加入路径以导入本地模块
sys.path.append(os.getcwd())

def test_search_engine(name, url):
    print(f"\n--- 测试搜索引擎: {name} ---")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ {name} 请求失败")
            return
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. 保存 HTML 供人工审计（如果需要）
        with open(f"app_logs/debug_{name}.html", "wb") as f:
            f.write(response.content)
        print(f"已保存 HTML 到 app_logs/debug_{name}.html")

        # 2. 模拟当前系统的提取逻辑
        links = []
        # 通用 A 标签提取
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(url, href)
            links.append(full_url)
            
        print(f"原始发现链接总数: {len(links)}")
        
        # 3. 模拟跳转链接识别
        matches = []
        redirect_patterns = ["bing.com/ck/a", "duckduckgo.com/l/", "google.com/url"]
        for l in links:
            if any(p in l.lower() for p in redirect_patterns):
                matches.append(l)
        
        print(f"符合跳转特征的链接数: {len(matches)}")
        if matches:
            print("样例链接:")
            for m in matches[:3]:
                print(f"  - {m[:100]}...")
        else:
            print("⚠️ 未发现任何搜索结果跳转链接！")
            # 尝试通过文本内容查找
            content_links = []
            for a in soup.find_all('a', href=True):
                # 排除本域且非广告
                parsed = urlparse(urljoin(url, a['href']))
                if parsed.netloc and parsed.netloc not in url:
                    content_links.append(urljoin(url, a['href']))
            print(f"非本站域名的链接数: {len(content_links)}")
            if content_links:
                for cl in content_links[:3]:
                    print(f"  - {cl[:100]}...")

    except Exception as e:
        print(f"❌ 发生异常: {e}")

if __name__ == "__main__":
    kw = "数据分析"
    from urllib.parse import quote
    q = quote(kw)
    
    test_search_engine("Bing", f"https://www.bing.com/search?q={q}")
    test_search_engine("DuckDuckGo", f"https://html.duckduckgo.com/html/?q={q}")
