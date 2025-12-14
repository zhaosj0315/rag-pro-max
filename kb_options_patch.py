#!/usr/bin/env python3
"""
知识库高级选项补丁
用于替换主应用中的高级选项部分，添加OCR和摘要控制
"""

# 这个补丁用于替换 src/apppro.py 中第1065-1076行的高级选项部分

ORIGINAL_CODE = '''
            # 高级选项
            with st.expander("🔧 高级选项", expanded=True):
                adv_col1, adv_col2 = st.columns(2)
                with adv_col1:
                    force_reindex = st.checkbox("🔄 强制重建索引", False, help="删除现有索引，重新构建（用于修复损坏的索引）")
                with adv_col2:
                    extract_metadata = st.checkbox(
                        "📊 提取元数据", 
                        value=False,
                        help="开启后提取文件分类、关键词等信息，但会降低 30% 处理速度"
                    )
'''

REPLACEMENT_CODE = '''
            # 高级选项 - 增强版
            with st.expander("🔧 高级选项", expanded=True):
                # 第一行：原有选项
                adv_col1, adv_col2 = st.columns(2)
                with adv_col1:
                    force_reindex = st.checkbox("🔄 强制重建索引", False, help="删除现有索引，重新构建（用于修复损坏的索引）")
                with adv_col2:
                    extract_metadata = st.checkbox(
                        "📊 提取元数据", 
                        value=False,
                        help="开启后提取文件分类、关键词等信息，但会降低 30% 处理速度"
                    )
                
                # 第二行：新增OCR和摘要选项
                st.write("")
                ocr_col1, ocr_col2 = st.columns(2)
                
                with ocr_col1:
                    use_ocr = st.checkbox(
                        "🔍 启用OCR识别",
                        value=st.session_state.get('use_ocr', True),
                        help="对PDF中的图片和扫描文档进行文字识别（耗时较长）",
                        key="kb_use_ocr"
                    )
                    st.session_state.use_ocr = use_ocr
                
                with ocr_col2:
                    generate_summary = st.checkbox(
                        "📝 生成文档摘要",
                        value=st.session_state.get('generate_summary', False),
                        help="为每个文档生成AI摘要（需要LLM支持）",
                        key="kb_generate_summary"
                    )
                    st.session_state.generate_summary = generate_summary
                
                # 处理模式提示
                st.write("")
                if use_ocr and generate_summary:
                    st.info("🔍📝 **完整处理模式**：OCR识别 + 摘要生成（处理时间较长，功能最全面）")
                elif use_ocr:
                    st.info("🔍 **OCR模式**：启用图片文字识别（适合扫描文档和图片较多的PDF）")
                elif generate_summary:
                    st.info("📝 **摘要模式**：生成文档摘要（便于快速了解文档内容）")
                else:
                    st.success("⚡ **快速模式**：跳过OCR和摘要，处理速度最快")
'''

print("知识库高级选项补丁")
print("=" * 50)
print("请在 src/apppro.py 中找到第1065-1076行的高级选项部分")
print("将其替换为以下代码：")
print()
print(REPLACEMENT_CODE)
print()
print("这样用户就可以在构建知识库时选择：")
print("- 🔍 是否启用OCR识别")
print("- 📝 是否生成文档摘要")
print("- 🔄 是否强制重建索引")
print("- 📊 是否提取元数据")
print()
print("所有选项都在一个地方，用户体验更好！")
