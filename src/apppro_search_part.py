                # 获取搜索参数
                crawl_depth = st.session_state.get('search_crawl_depth', 2)
                max_pages = st.session_state.get('search_max_pages', 5)
                parser_type = st.session_state.get('search_parser_type', 'default')
                quality_threshold = st.session_state.get('quality_threshold', 45.0)
                
                st.info(f"🔍 开始全网智能搜索: {search_keyword}")
                
                # --- 🔥 核心改进：使用真正的搜索引擎获取初始链接 ---
                def perform_real_search(keyword, limit=5):
                    """使用 DuckDuckGo 获取真实搜索结果"""
                    from ddgs import DDGS
                    try:
                        logger.info(f"🌐 调用搜索引擎获取关键词 '{keyword}' 的结果...")
                        with DDGS() as ddgs:
                            # 增加超时控制和重试
                            results = list(ddgs.text(keyword, max_results=limit))
                            if results:
                                return [r.get('href') for r in results if r.get('href')]
                    except Exception as e:
                        logger.error(f"搜索引擎调用失败: {e}")
                    return []

                def get_fallback_search_engines(keyword):
                    """根据关键词智能选择预定义搜索引擎作为备份"""
                    keyword_lower = keyword.lower()
                    medical_keywords = ['cancer', 'disease', 'medicine', 'health', 'treatment', 'diagnosis', '癌症', '疾病', '医学', '健康', '治疗', '诊断', '药物', '症状', '病理']
                    tech_keywords = ['python', 'java', 'javascript', 'programming', 'coding', 'algorithm', '编程', '代码', '算法', '开发', '软件', '技术']
                    
                    if any(med_word in keyword_lower for med_word in medical_keywords):
                        return ["https://zh.wikipedia.org/", "https://baike.baidu.com/", "https://www.39.net/", "https://www.xywy.com/"]
                    elif any(tech_word in keyword_lower for tech_word in tech_keywords):
                        return ["https://www.runoob.com/", "https://docs.python.org/zh-cn/3/", "https://help.aliyun.com/", "https://www.zhihu.com/"]
                    else:
                        return ["https://zh.wikipedia.org/", "https://baike.baidu.com/", "https://www.zhihu.com/"]

                # 优先使用真实搜索
                start_urls = perform_real_search(search_keyword, limit=max_pages)
                
                if not start_urls:
                    st.warning("⚠️ 实时搜索受阻，尝试使用专业站点进行深度挖掘...")
                    start_urls = get_fallback_search_engines(search_keyword)
                
                # 生成唯一输出目录
                from datetime import datetime
                timestamp_dir = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_output_dir = os.path.join("temp_uploads", f"Search_{search_keyword.replace(' ', '_')}_{timestamp_dir}")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_status(msg):
                    status_text.text(f"🔍 {msg}")
                    logger.info(f"🔍 智能搜索: {msg}")
                
                logger.info(f"🔍 启动抓取引擎: {search_keyword} (深度:{crawl_depth}, 广度:{max_pages})")
                
                with st.spinner("深度挖掘内容中..."):
                    from src.processors.concurrent_crawler import ConcurrentCrawler
                    concurrent_crawler = ConcurrentCrawler(max_workers=4, use_processes=False) # 适度增加并发
                    
                    def enhanced_progress_callback(message, progress=None):
                        update_status(message)
                        if progress is not None:
                            progress_bar.progress(progress)
                    
                    # 执行并发爬取
                    crawl_results = concurrent_crawler.crawl_with_depth(
                        start_urls,
                        max_depth=crawl_depth,
                        max_pages_per_level=max_pages,
                        progress_callback=enhanced_progress_callback
                    )
