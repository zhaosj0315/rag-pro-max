#!/usr/bin/env python3
"""
改进的用户友好错误处理器
提供更好的错误提示和用户引导
"""

import streamlit as st
from typing import Optional

class FriendlyErrorHandler:
    """友好的错误处理器"""
    
    # 错误类型和对应的友好提示
    ERROR_GUIDANCE = {
        "知识库未加载": {
            "title": "知识库未准备好",
            "message": "当前没有可用的知识库",
            "solutions": [
                "请先在左侧选择一个知识库",
                "如果没有知识库，点击'➕ 新建知识库'创建一个",
                "确保知识库已成功加载（显示绿色✅状态）"
            ],
            "icon": "📚"
        },
        
        "文件上传": {
            "title": "文件上传遇到问题",
            "message": "文件无法正常上传或处理",
            "solutions": [
                "检查文件格式是否支持（PDF、DOCX、TXT、MD等）",
                "确认文件大小不超过限制（通常50MB以内）",
                "尝试重新选择文件或刷新页面",
                "如果是网络问题，请稍后重试"
            ],
            "icon": "📁"
        },
        
        "查询失败": {
            "title": "查询处理失败",
            "message": "系统无法处理您的问题",
            "solutions": [
                "请尝试重新表述您的问题",
                "确认知识库中有相关内容",
                "检查网络连接是否正常",
                "如果问题持续，请尝试刷新页面"
            ],
            "icon": "🔍"
        },
        
        "配置错误": {
            "title": "配置设置有误",
            "message": "系统配置存在问题",
            "solutions": [
                "检查API密钥是否正确设置",
                "确认模型服务是否可用",
                "尝试使用'⚡ 一键配置'恢复默认设置",
                "查看配置页面的连接测试结果"
            ],
            "icon": "⚙️"
        },
        
        "网络连接": {
            "title": "网络连接问题",
            "message": "无法连接到所需的服务",
            "solutions": [
                "检查您的网络连接",
                "确认防火墙没有阻止连接",
                "如果使用代理，请检查代理设置",
                "稍后重试或联系网络管理员"
            ],
            "icon": "🌐"
        }
    }
    
    @classmethod
    def show_friendly_error(cls, error_type: str, specific_message: str = "", 
                           custom_solutions: Optional[list] = None):
        """显示友好的错误信息"""
        
        guidance = cls.ERROR_GUIDANCE.get(error_type, {
            "title": "遇到了问题",
            "message": "系统运行时出现异常",
            "solutions": ["请尝试刷新页面", "如果问题持续，请联系技术支持"],
            "icon": "⚠️"
        })
        
        # 创建友好的错误显示
        with st.container():
            col1, col2 = st.columns([1, 10])
            
            with col1:
                st.markdown(f"## {guidance['icon']}")
            
            with col2:
                st.error(f"**{guidance['title']}**")
                
                if specific_message:
                    st.write(f"详细信息：{specific_message}")
                else:
                    st.write(guidance['message'])
                
                # 显示解决方案
                st.markdown("**💡 解决建议：**")
                solutions = custom_solutions or guidance['solutions']
                
                for i, solution in enumerate(solutions, 1):
                    st.write(f"{i}. {solution}")
                
                # 添加帮助链接
                with st.expander("🆘 需要更多帮助？"):
                    st.write("如果上述建议无法解决问题，您可以：")
                    st.write("• 查看用户手册了解详细操作步骤")
                    st.write("• 检查常见问题解答（FAQ）")
                    st.write("• 尝试重启应用程序")
    
    @classmethod
    def show_validation_error(cls, field_name: str, issue: str, suggestion: str):
        """显示输入验证错误"""
        st.error(f"**输入验证失败**")
        st.write(f"字段：{field_name}")
        st.write(f"问题：{issue}")
        st.info(f"💡 建议：{suggestion}")
    
    @classmethod
    def show_operation_failed(cls, operation: str, reason: str, retry_action: str = ""):
        """显示操作失败错误"""
        with st.container():
            st.error(f"**{operation}失败**")
            st.write(f"原因：{reason}")
            
            if retry_action:
                st.info(f"💡 请尝试：{retry_action}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 重试", key=f"retry_{operation}"):
                    st.rerun()
            with col2:
                if st.button("❓ 获取帮助", key=f"help_{operation}"):
                    st.info("请查看用户手册或联系技术支持")

# 便捷函数
def friendly_error(error_type: str, message: str = "", solutions: list = None):
    """便捷的友好错误显示函数"""
    FriendlyErrorHandler.show_friendly_error(error_type, message, solutions)

def validation_error(field: str, issue: str, suggestion: str):
    """便捷的验证错误显示函数"""
    FriendlyErrorHandler.show_validation_error(field, issue, suggestion)

def operation_failed(operation: str, reason: str, retry_action: str = ""):
    """便捷的操作失败显示函数"""
    FriendlyErrorHandler.show_operation_failed(operation, reason, retry_action)
