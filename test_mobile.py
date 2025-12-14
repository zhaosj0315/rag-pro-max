"""
移动端适配测试页面
用于验证移动端优化效果
"""

import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.mobile_responsive import apply_mobile_optimizations, mobile_chat_interface, mobile_file_upload

st.set_page_config(
    page_title="移动端测试",
    page_icon="📱",
    layout="wide"
)

# 应用移动端优化
apply_mobile_optimizations()

st.title("📱 移动端适配测试")

st.markdown("""
### 测试说明
1. 点击侧边栏的 **"📱 移动端模式"** 按钮启用移动端优化
2. 在手机浏览器中访问此页面测试效果
3. 测试各种功能的移动端适配情况

### 测试功能
- ✅ 响应式布局
- ✅ 触摸优化按钮
- ✅ 移动端聊天界面
- ✅ 文件上传适配
- ✅ 字体大小优化
""")

# 测试移动端聊天界面
user_input, send_button, clear_button = mobile_chat_interface()

if user_input and send_button:
    st.success(f"📤 发送消息: {user_input}")

# 测试移动端文件上传
uploaded_file = mobile_file_upload()
if uploaded_file:
    st.success(f"📁 文件上传: {uploaded_file.name}")

# 测试响应式按钮
st.markdown("### 按钮测试")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("按钮1", use_container_width=True):
        st.toast("按钮1被点击")

with col2:
    if st.button("按钮2", use_container_width=True):
        st.toast("按钮2被点击")

with col3:
    if st.button("按钮3", use_container_width=True):
        st.toast("按钮3被点击")

# 测试表单
st.markdown("### 表单测试")
with st.form("mobile_test_form"):
    name = st.text_input("姓名")
    email = st.text_input("邮箱")
    message = st.text_area("消息", height=100)
    
    if st.form_submit_button("提交", use_container_width=True):
        st.success("表单提交成功！")

# 显示当前模式
if st.session_state.get('mobile_mode', False):
    st.success("✅ 当前处于移动端模式")
else:
    st.info("💻 当前处于桌面端模式")

st.markdown("---")
st.markdown("**测试完成后，请在实际手机上访问主应用验证效果**")
