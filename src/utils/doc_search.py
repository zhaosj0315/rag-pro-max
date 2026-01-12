import os
import glob
from typing import List, Dict

def search_docs(keyword: str) -> List[Dict]:
    """
    搜索项目根目录下的 Markdown 文档内容
    """
    results = []
    if not keyword:
        return results
        
    # 获取根目录下所有 MD 文件
    md_files = glob.glob("*.md")
    
    for file_path in md_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if keyword.lower() in content.lower() or keyword.lower() in file_path.lower():
                    # 提取标题（第一行）
                    title = content.split('\n')[0].replace('#', '').strip()
                    if not title:
                        title = file_path
                        
                    # 提取预览片段
                    idx = content.lower().find(keyword.lower())
                    start = max(0, idx - 50)
                    end = min(len(content), idx + 150)
                    preview = "..." + content[start:end].replace('\n', ' ') + "..."
                    
                    results.append({
                        "title": title,
                        "file": file_path,
                        "preview": preview
                    })
        except:
            continue
            
    return results[:10] # 仅返回前10条
