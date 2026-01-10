"""
HTML 转 Markdown 工具
用于将网页内容转换为结构化的 Markdown 格式
"""

from bs4 import BeautifulSoup, NavigableString, Tag
import re

class HtmlToMarkdown:
    def __init__(self):
        pass
        
    @staticmethod
    def convert(html_content: str) -> str:
        """转换HTML字符串为Markdown (智能提取正文)"""
        if not html_content:
            return ""
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. 深度清理: 移除已知噪声标签和类
        HtmlToMarkdown._clean_soup(soup)
            
        # 2. 智能提取正文区域
        content_soup = HtmlToMarkdown._extract_main_content(soup)
        
        # 3. 二次清理: 针对提取出的内容再次进行清理 (防止提取了父容器导致噪声残留)
        HtmlToMarkdown._clean_soup(content_soup)
            
        # 4. 递归处理转换为Markdown
        markdown = HtmlToMarkdown._process_element(content_soup).strip()
        
        # 5. 最终优化
        # 压缩多余换行 (3个以上换行 -> 2个)
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        # 移除行首尾空白
        markdown = "\n".join([line.rstrip() for line in markdown.splitlines()])
        
        return markdown

    @staticmethod
    def _clean_soup(soup):
        """移除不需要的标签和CSS类"""
        if not soup:
            return

        # A. 移除标签
        for tag in soup(['script', 'style', 'meta', 'link', 'noscript', 'iframe', 'svg', 'canvas', 
                        'nav', 'footer', 'header', 'aside', 'form', 'button', 'input', 'textarea', 'select',
                        'dialog', 'menu']):
            tag.decompose()

        # B. 移除特定的ID和Class (CSS选择器模式)
        # 包含: 广告, 侧边栏, 社交分享, 弹窗, 页眉页脚, 导航
        noise_selectors = [
            # 通用噪声
            '.ad', '.advertisement', '.banner', '.social-share', '.share-buttons',
            '.sidebar', '.widget', '.popup', '.cookie-consent', '.modal',
            '.nav', '.navbar', '.navigation', '.menu', '.breadcrumb',
            '.footer', '.copyright', '.related-posts', '.comments', '.reply',
            '.hidden', '.print-only', '.sr-only', '.visually-hidden',
            
            # Wikipedia / MediaWiki 专用
            '.mw-editsection',       # [编辑] 链接
            '.mw-jump-link',         # 跳转链接
            '.mw-indicators',        # 顶部小图标
            '.printfooter',          # 打印版页脚
            '.catlinks',             # 底部分类链接
            '.noprint',              # 不打印的内容
            '.mw-cite-backlink',     # 引用反向链接
            '#siteNotice',           # 站点公告
            '#mw-navigation',        # 导航栏
            '#mw-page-base',         # 顶部基础条
            '#mw-head-base',         # 顶部头
            '#mw-head',              # 顶部头
            '#mw-panel',             # 左侧边栏
            '#footer',               # 页脚
            '.vector-menu',          # Vector 皮肤菜单
            '.vector-header',        # Vector 皮肤头
            '.portal',               # 语言/其他门户链接
            '#p-lang',               # 语言列表
            '.interlanguage-link',   # 跨语言链接
            '.reference-distributor' # 参考分发
        ]
        
        for selector in noise_selectors:
            for element in soup.select(selector):
                element.decompose()
                
        # C. 移除空的容器标签 (减少空白噪音)
        # 注意: 需谨慎, 有些空标签可能是占位符, 但在Markdown中无意义
        for tag in soup.find_all(['div', 'span', 'p', 'section']):
            if not tag.get_text(strip=True) and not tag.find(['img', 'iframe']):
                tag.decompose()

    @staticmethod
    def _extract_main_content(soup):
        """提取主要内容区域"""
        # 1. 尝试常用内容选择器 (优先级从高到低)
        content_selectors = [
            # Wikipedia / MediaWiki 核心内容区
            '#bodyContent', 
            '.mw-parser-output',
            
            # 常见语义化标签
            'article', 'main', '[role="main"]',
            
            # 常见正文容器 Class/ID
            '.article-body', '.post-body', '.content-body',
            '.article', '.content', '.post', '.main-content', 
            '#content', '#main', '.article-content', '.post-content',
            
            # 特定平台/框架
            '.markdown-body', '.doc-content', '.documentation',
            '.ContentBody', '.main-text', '.news-content', '#artical_real',
            '.rich_media_content', '.answer-text', '.zm-item-rich-text'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                # 检查提取的内容是否太少 (防止误判提取了空的容器)
                if len(element.get_text(strip=True)) > 50:
                    return element
        
        # 2. 如果没找到，尝试基于文本密度的启发式算法
        # 寻找包含最多P标签的容器
        max_p_count = 0
        best_container = None
        
        for tag in soup.find_all(['div', 'section', 'td']):
            # 计算直接子P标签数量（或者稍微深一层）
            p_count = len(tag.find_all('p', recursive=False))
            # 也可以计算总文本长度
            text_len = len(tag.get_text())
            
            if p_count > 2 and text_len > 200: # 阈值过滤
                score = p_count * 50 + text_len
                if p_count > max_p_count:
                    max_p_count = p_count
                    best_container = tag
        
        if best_container:
            return best_container
            
        # 3. 实在找不到，返回body或整个soup
        return soup.body if soup.body else soup
    
    @staticmethod
    def _process_element(element) -> str:
        """处理单个元素"""
        if isinstance(element, NavigableString):
            text = element.strip()
            # 简单的文本清理，避免过多的空白
            return re.sub(r'\s+', ' ', text) if text else ""
            
        if not isinstance(element, Tag):
            return ""
            
        content = ""
        
        # 处理子元素
        for child in element.children:
            child_text = HtmlToMarkdown._process_element(child)
            if child_text:
                # 智能添加空格或换行
                if content and not content.endswith('\n') and not child_text.startswith('\n'):
                    # 如果前一个字符不是空格，添加空格
                    if not content[-1].isspace():
                        content += " "
                content += child_text
        
        # 根据标签类型格式化
        tag_name = element.name.lower()
        
        if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(tag_name[1])
            return f"\n\n{'#' * level} {content}\n\n"
            
        elif tag_name == 'p':
            if not content.strip(): return ""
            return f"\n\n{content}\n\n"
            
        elif tag_name == 'br':
            return "\n"
            
        elif tag_name in ['ul', 'ol']:
            return f"\n{content}\n"
            
        elif tag_name == 'li':
            # 检查父标签是ul还是ol
            parent = element.parent
            if parent and parent.name == 'ol':
                return f"\n1. {content}"
            else:
                return f"\n- {content}"
                
        elif tag_name == 'pre':
            # 代码块
            code_content = element.get_text().strip()
            return f"\n\n```\n{code_content}\n```\n\n"
            
        elif tag_name == 'code':
            if element.parent.name == 'pre':
                return content
            return f"`{content}`"
            
        elif tag_name == 'blockquote':
            return f"\n\n> {content}\n\n"
            
        elif tag_name == 'a':
            href = element.get('href', '')
            if href and content:
                # 移除可能的换行符
                content = content.replace('\n', ' ')
                return f"[{content}]({href})"
            return content
            
        elif tag_name == 'img':
            src = element.get('src', '')
            alt = element.get('alt', 'image').replace('\n', ' ')
            if src:
                return f"\n![{alt}]({src})\n"
            return ""
            
        elif tag_name == 'table':
            return f"\n\n{HtmlToMarkdown._process_table(element)}\n\n"
            
        elif tag_name in ['div', 'section', 'article', 'main']:
            return f"\n{content}\n"
            
        elif tag_name in ['b', 'strong']:
            return f"**{content}**"
            
        elif tag_name in ['i', 'em']:
            return f"*{content}*"
            
        else:
            return content

    @staticmethod
    def _process_table(table_tag) -> str:
        """处理表格"""
        rows = []
        
        # 处理表头
        headers = []
        thead = table_tag.find('thead')
        if thead:
            for th in thead.find_all('th'):
                headers.append(th.get_text().strip())
        else:
            # 尝试在第一行查找th
            first_row = table_tag.find('tr')
            if first_row:
                for th in first_row.find_all(['th', 'td']):
                    headers.append(th.get_text().strip())
        
        if not headers:
            return ""
            
        # 构建Markdown表头
        header_row = "| " + " | ".join(headers) + " |"
        separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"
        rows.append(header_row)
        rows.append(separator_row)
        
        # 处理表体
        tbody = table_tag.find('tbody')
        data_rows = tbody.find_all('tr') if tbody else table_tag.find_all('tr')
        
        # 如果第一行被用作表头，跳过它
        if not thead and data_rows:
            data_rows = data_rows[1:]
            
        for tr in data_rows:
            cols = []
            for td in tr.find_all(['td', 'th']):
                # 移除换行符，防止破坏表格格式
                cell_text = td.get_text().strip().replace('\n', '<br>')
                cols.append(cell_text)
            
            # 补齐列数
            while len(cols) < len(headers):
                cols.append("")
            
            if cols:
                rows.append("| " + " | ".join(cols[:len(headers)]) + " |")
                
        return "\n".join(rows)
