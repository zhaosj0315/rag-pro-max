import streamlit as st

def enable_auto_scroll():
    """
    注入 JavaScript 以实现流式输出时的自动滚动。
    使用 MutationObserver 监听 DOM 变化，确保视图始终跟随最新内容。
    """
    # 定义 JavaScript 代码
    js_code = """
    <script>
    (function() {
        if (window.autoScrollObserver) return;

        function getScrollContainer() {
            return window; 
        }

        function scrollToBottom() {
            window.scrollTo({
                top: document.body.scrollHeight,
                behavior: "smooth"
            });
        }

        const observer = new MutationObserver((mutations) => {
            let shouldScroll = false;
            for (const mutation of mutations) {
                if (mutation.type === 'childList' || mutation.type === 'characterData') {
                    shouldScroll = true;
                    break;
                }
            }
            if (shouldScroll) {
                scrollToBottom();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true,
            attributes: true, 
            attributeFilter: ['style', 'class']
        });

        window.autoScrollObserver = observer;
        setTimeout(scrollToBottom, 100);
        console.log("Auto-scroll observer activated 🚀");
    })();
    </script>
    """
    
    try:
        if hasattr(st, "html"):
            st.html(js_code)
        else:
            st.markdown(js_code, unsafe_allow_html=True)
    except Exception:
        st.markdown(js_code, unsafe_allow_html=True)
