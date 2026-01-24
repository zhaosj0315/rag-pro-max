import streamlit.components.v1 as components

def inject_scroll_buttons():
    """
    注入悬浮滚动按钮 (回到顶部/直达底部)
    使用纯 CSS/JS 实现，无 Streamlit 状态交互，性能极佳。
    """
    
    # 定义 HTML/CSS/JS
    scroll_code = """
    <style>
        /* 容器定位：右下角，但在 Streamlit 页脚之上 */
        .scroll-btn-container {
            position: fixed;
            bottom: 100px;
            right: 25px;
            z-index: 999999;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        /* 按钮通用样式 */
        .scroll-btn {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background-color: rgba(255, 255, 255, 0.9);
            color: #333;
            border: 1px solid #e0e0e0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
            font-size: 18px;
            user-select: none;
            backdrop-filter: blur(4px);
        }

        /* 悬浮效果 */
        .scroll-btn:hover {
            transform: translateY(-2px) scale(1.05);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            background-color: #ffffff;
            border-color: #2196f3; /* 极光蓝 */
            color: #2196f3;
        }

        /* 点击效果 */
        .scroll-btn:active {
            transform: translateY(0) scale(0.95);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* 黑暗模式适配 (根据 data-theme 属性或 media query) */
        @media (prefers-color-scheme: dark) {
            .scroll-btn {
                background-color: rgba(40, 44, 52, 0.85);
                color: #e0e0e0;
                border-color: #444;
            }
            .scroll-btn:hover {
                background-color: rgba(50, 54, 62, 1);
                color: #4da6ff;
                border-color: #4da6ff;
            }
        }
    </style>

    <div class="scroll-btn-container">
        <!-- 回到顶部按钮 -->
        <div class="scroll-btn" onclick="scrollToTop()" title="回到顶部 (Top)">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M18 15l-6-6-6 6"/>
            </svg>
        </div>
        
        <!-- 直达底部按钮 -->
        <div class="scroll-btn" onclick="scrollToBottom()" title="直达底部 (Bottom)">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 9l6 6 6-6"/>
            </svg>
        </div>
    </div>

    <script>
        // 平滑滚动到顶部
        function scrollToTop() {
            window.parent.document.documentElement.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        }

        // 平滑滚动到底部
        function scrollToBottom() {
            // 尝试找到 Streamlit 的主容器
            const mainContainer = window.parent.document.querySelector('.main');
            if (mainContainer) {
                // 如果能找到主容器，可能需要滚动它（取决于布局）
                // 但通常 scroll 发生在 documentElement 或 body 上
            }
            
            window.parent.document.documentElement.scrollTo({
                top: window.parent.document.documentElement.scrollHeight,
                behavior: 'smooth'
            });
        }
    </script>
    """
    
    # 注入到 Streamlit 页面中
    # height=0 确保它不占位，只负责注入 fixed 定位的元素
    components.html(scroll_code, height=0, width=0)
