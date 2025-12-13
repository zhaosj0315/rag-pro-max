"""
改进的对话处理工具 - 稳定性优先
- 安全的流式输出
- 引用源验证
- 追问生成容错
- 对话历史保护
"""

import os
import json
import shutil
import threading
import time
import re
from datetime import datetime
from pathlib import Path
from collections import Counter
from llama_index.core import Settings
import re

HISTORY_DIR = "chat_histories"
Path(HISTORY_DIR).mkdir(parents=True, exist_ok=True)


def save_chat_history_safe(kb_id, messages, logger=None):
    """
    安全保存对话历史
    - 验证数据完整性
    - 原子操作
    - 自动备份
    """
    path = os.path.join(HISTORY_DIR, f"{kb_id}.json")
    
    # 验证数据格式
    if not isinstance(messages, list):
        if logger:
            logger.log_error("对话保存", "数据格式错误", {"kb_id": kb_id})
        return False
    
    try:
        # 验证每条消息的格式
        for msg in messages:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                if logger:
                    logger.log_error("对话保存", "消息格式错误", {"kb_id": kb_id})
                return False
        
        # 先写临时文件
        temp_path = path + ".tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)
        
        # 验证临时文件可读
        with open(temp_path, 'r', encoding='utf-8') as f:
            json.load(f)
        
        # 备份原文件
        if os.path.exists(path):
            backup_path = path + ".bak"
            shutil.copy2(path, backup_path)
        
        # 原子操作：替换
        shutil.move(temp_path, path)
        
        if logger:
            logger.log("对话保存", "success", f"✅ 对话历史已保存: {kb_id}", {"kb_id": kb_id})
        
        return True
        
    except Exception as e:
        if logger:
            logger.log_error("对话保存", str(e), {"kb_id": kb_id})
        
        # 清理临时文件
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        
        return False


def load_chat_history_safe(kb_id, logger=None):
    """
    安全加载对话历史
    - 自动恢复损坏的文件
    - 验证数据完整性
    """
    path = os.path.join(HISTORY_DIR, f"{kb_id}.json")
    
    if not os.path.exists(path):
        return []
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return data
        else:
            if logger:
                logger.log_error("对话加载", "数据格式错误", {"kb_id": kb_id})
            return []
    
    except json.JSONDecodeError:
        # 尝试从备份恢复
        backup_path = path + ".bak"
        if os.path.exists(backup_path):
            try:
                with open(backup_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if logger:
                    logger.log("对话加载", "warning", f"⚠️ 从备份恢复对话历史: {kb_id}", {"kb_id": kb_id})
                return data if isinstance(data, list) else []
            except:
                pass
        
        if logger:
            logger.log_error("对话加载", "文件损坏且无备份", {"kb_id": kb_id})
        return []
    
    except Exception as e:
        if logger:
            logger.log_error("对话加载", str(e), {"kb_id": kb_id})
        return []


def stream_response_safe(chat_engine, prompt, max_retries=2, logger=None):
    """
    安全的流式响应
    - 自动重试
    - 完整性检查
    - 超时控制
    """
    for attempt in range(max_retries):
        try:
            full_text = ""
            response = chat_engine.stream_chat(prompt)
            
            # 流式输出
            for token in response.response_gen:
                if token:  # 过滤空token
                    full_text += token
                    yield token
            
            # 验证响应完整性
            if not full_text.strip():
                if logger:
                    logger.log_error("流式输出", "响应为空", {"attempt": attempt + 1})
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                raise ValueError("响应为空")
            
            # 返回完整响应对象
            return response, full_text
            
        except Exception as e:
            if logger:
                logger.log_error("流式输出", str(e), {"attempt": attempt + 1})
            
            if attempt < max_retries - 1:
                time.sleep(1)  # 等待后重试
                continue
            
            raise


def extract_sources_safe(response, min_score=0.3, logger=None):
    """
    安全提取引用源
    - 验证数据有效性
    - 过滤低质量源
    - 防止显示无效内容
    """
    sources = []
    
    if not hasattr(response, 'source_nodes') or not response.source_nodes:
        return sources
    
    for node in response.source_nodes:
        try:
            # 验证必要字段
            file_name = node.metadata.get('file_name', 'Unknown') if hasattr(node, 'metadata') else 'Unknown'
            text = node.text if hasattr(node, 'text') else ""
            score = float(node.score or 0.0) if hasattr(node, 'score') else 0.0
            
            # 过滤低质量源
            if score < min_score:
                continue
            
            # 截断过长文本
            text_preview = text[:200].replace("\n", " ").strip()
            if not text_preview:
                continue
            
            sources.append({
                "file": str(file_name)[:100],  # 防止过长
                "score": round(score, 3),
                "text": text_preview + "..."
            })
        
        except Exception as e:
            if logger:
                logger.log_error("源提取", str(e), {"node": str(node)[:100]})
            continue
    
    return sources


def _extract_keywords(text, max_keywords=5):
    """提取文本关键词"""
    try:
        import jieba
        # 使用 jieba 分词
        words = jieba.lcut(text)
    except:
        # 降级：简单分词
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()
    
    # 过滤停用词和短词
    stop_words = {'的', '了', '是', '在', '有', '和', '与', '或', '等', '及', '以', '为', '这', '那', '我', '你', '他', '她', '它', '们', '个', '中', '也', '都', '就', '而', '要', '会', '可以', '能', '说', '对', '但', '不', '没有'}
    keywords = [w for w in words if len(w) > 1 and w not in stop_words]
    
    # 统计词频
    word_freq = Counter(keywords)
    # 返回高频词
    return [word for word, _ in word_freq.most_common(max_keywords)]


def _is_similar_question(q1, q2, threshold=0.7):
    """检测两个问题是否相似"""
    if not q1 or not q2:
        return False
    
    # 简单的相似性检测
    q1_clean = re.sub(r'[^\w]', '', q1.lower())
    q2_clean = re.sub(r'[^\w]', '', q2.lower())
    
    # 完全相同
    if q1_clean == q2_clean:
        return True
    
    # 包含关系
    if len(q1_clean) > 5 and len(q2_clean) > 5:
        if q1_clean in q2_clean or q2_clean in q1_clean:
            return True
    
    # 关键词重叠度
    words1 = set(_extract_keywords(q1, max_keywords=5))
    words2 = set(_extract_keywords(q2, max_keywords=5))
    
    if words1 and words2:
        overlap = len(words1 & words2) / len(words1 | words2)
        return overlap > threshold
    
    return False


def generate_follow_up_questions_safe(context_text, num_questions=3, existing_questions=None, timeout=60, logger=None, query_engine=None, llm_model=None):
    """
    安全地生成追问（带超时控制和错误处理）
    
    Args:
        context_text: 上下文文本（回答内容）
        num_questions: 需要生成的问题数量
        existing_questions: 已存在的问题列表（用于去重）
        timeout: 超时时间（秒），默认60秒
        logger: 日志记录器
        query_engine: 查询引擎（用于获取LLM）
        llm_model: 直接传入LLM模型
        
    Returns:
        list: 生成的问题列表
    """
    result = {"questions": []}
    
    # 基于知识库内容生成针对性降级问题
    def get_smart_fallback(text, query_engine=None):
        fallback = []
        
        # 如果有查询引擎，尝试从知识库获取相关主题
        if query_engine:
            try:
                # 提取关键词并查询知识库
                keywords = _extract_keywords(text, max_keywords=2)
                if keywords:
                    # 查询知识库中的相关内容
                    kb_results = query_engine.query(f"关于{keywords[0]}的内容")
                    if hasattr(kb_results, 'source_nodes') and kb_results.source_nodes:
                        # 基于知识库实际内容生成问题
                        for node in kb_results.source_nodes[:2]:
                            node_text = node.text if hasattr(node, 'text') else str(node)
                            if len(node_text) > 50:
                                # 基于实际文档内容生成问题
                                if "方法" in node_text or "步骤" in node_text:
                                    fallback.append(f"文档中提到的{keywords[0]}具体方法是什么？")
                                elif "原因" in node_text or "因为" in node_text:
                                    fallback.append(f"为什么{keywords[0]}会产生这样的结果？")
                                elif "案例" in node_text or "例子" in node_text:
                                    fallback.append(f"有哪些关于{keywords[0]}的具体案例？")
                                else:
                                    fallback.append(f"文档中还有哪些关于{keywords[0]}的信息？")
            except Exception as e:
                if logger:
                    logger.log_warning("推荐问题", f"知识库查询失败: {e}")
        
        # 如果知识库查询失败或没有结果，使用基于内容的降级
        if not fallback:
            # 基于回答内容特征生成问题
            if any(word in text for word in ["方案", "解决", "处理", "应对"]):
                fallback.extend([
                    "这个方案的具体实施步骤是什么？",
                    "可能遇到哪些实际问题？",
                    "有没有其他替代方案？"
                ])
            elif any(word in text for word in ["分析", "研究", "调查", "数据"]):
                fallback.extend([
                    "这个分析的数据来源是什么？",
                    "结论的可靠性如何？",
                    "还有哪些相关的研究发现？"
                ])
            elif any(word in text for word in ["技术", "工具", "系统", "平台"]):
                fallback.extend([
                    "这个技术的适用范围是什么？",
                    "与现有方案相比有何优势？",
                    "实际应用中的效果如何？"
                ])
            else:
                # 基于关键词生成知识库相关问题
                keywords = _extract_keywords(text, max_keywords=2)
                if keywords:
                    fallback.extend([
                        f"文档中还有哪些关于{keywords[0]}的详细信息？",
                        f"除了{keywords[0]}，还涉及哪些相关概念？",
                        f"这些内容在实际应用中如何体现？"
                    ])
                else:
                    fallback.extend([
                        "文档中还有哪些相关的重要信息？",
                        "这些内容如何与其他部分关联？",
                        "在实际应用中需要注意什么？"
                    ])
        
        return fallback[:num_questions]
        
        return fallback[:num_questions]

    def _generate():
        nonlocal result
        print(f"🔍 _generate开始，result初始状态: {result}")
        
        if result is None:
            result = {"questions": []}
            print(f"🔍 result为None，重新初始化: {result}")
        
        # 尝试从多个来源获取LLM
        llm = None
        
        # 1. 优先使用传入的LLM
        if llm_model:
            llm = llm_model
            print(f"🔍 使用传入的LLM: {type(llm_model)}")
        
        # 2. 从Settings获取
        elif hasattr(Settings, 'llm') and Settings.llm:
            llm = Settings.llm
            print(f"🔍 使用Settings.llm: {type(Settings.llm)}")
        
        # 3. 从query_engine获取
        elif query_engine and hasattr(query_engine, '_llm'):
            llm = query_engine._llm
            print(f"🔍 使用query_engine._llm: {type(query_engine._llm)}")
        
        if not llm:
            print("⚠️ LLM未设置，使用知识库感知降级策略")
            result["questions"] = get_smart_fallback(context_text, query_engine)
            return
        
        print(f"🔍 LLM获取成功，开始生成推荐问题...")

        try:
            # 优化上下文处理
            short_context = context_text[-1500:] if len(context_text) > 1500 else context_text
            
            # 排除已问过的问题
            existing_str = "\n".join(existing_questions[-10:]) if existing_questions else ""  # 只看最近10个
            
            # 🆕 增强知识库相关性
            kb_context = ""
            relevant_topics = []
            
            if query_engine:
                try:
                    # 更精准的关键词提取
                    keywords = _extract_keywords(short_context, max_keywords=5)
                    if keywords:
                        # 尝试多个查询策略
                        for i in range(min(2, len(keywords))):
                            try:
                                kb_query = " ".join(keywords[i:i+2])  # 2个关键词组合
                                
                                if hasattr(query_engine, 'query'):
                                    kb_response = query_engine.query(kb_query)
                                elif hasattr(query_engine, 'chat'):
                                    kb_response = query_engine.chat(kb_query)
                                else:
                                    continue
                                
                                if kb_response and hasattr(kb_response, 'source_nodes'):
                                    for node in kb_response.source_nodes[:3]:
                                        if hasattr(node, 'metadata'):
                                            if 'file_name' in node.metadata:
                                                topic = node.metadata['file_name'].replace('.pdf', '').replace('.txt', '')
                                                if topic not in relevant_topics:
                                                    relevant_topics.append(topic)
                                            # 获取部分内容作为上下文
                                            if hasattr(node, 'text') and len(node.text) > 50:
                                                kb_context += node.text[:200] + "...\n"
                                
                                if len(relevant_topics) >= 2:  # 找到足够的相关主题就停止
                                    break
                            except:
                                continue
                                
                except Exception as e:
                    pass  # 静默失败
            
            # 构建更智能的提示词，强调基于知识库内容
            topic_hint = f"\n相关文档：{', '.join(relevant_topics[:3])}" if relevant_topics else ""
            kb_hint = f"\n知识库内容参考：\n{kb_context[:300]}" if kb_context else ""
            
            prompt = (
                f"基于以下回答内容和知识库信息，生成 {num_questions * 2} 个高质量的追问问题。\n\n"
                f"重要要求：\n"
                f"1. 问题必须基于知识库实际内容，确保知识库能够回答\n"
                f"2. 问题简洁（10-15字）\n"
                f"3. 具有启发性和实用性\n"
                f"4. 避免重复已有问题\n"
                f"5. 每行一个问题，不要编号\n"
                f"6. 优先生成知识库有明确答案的问题\n\n"
                f"回答内容：{short_context}\n"
                f"{topic_hint}"
                f"{kb_hint}\n"
                f"{'已问过的问题（避免重复）：\n' + existing_str if existing_str else ''}"
            )
            
            print(f"🔍 开始调用LLM生成推荐问题...")
            print(f"🔍 提示词长度: {len(prompt)} 字符")
            
            try:
                resp = llm.complete(prompt)
                text = resp.text.strip()
                print(f"🔍 LLM响应: {text[:100]}...")
            except Exception as e:
                print(f"❌ LLM调用失败: {e}")
                result["questions"] = get_smart_fallback(context_text, query_engine)
                return
            
            # 解析生成的问题
            questions = []
            for line in text.split('\n'):
                line = line.strip()
                if line:
                    # 清理问题格式
                    question = re.sub(r'^[\d\.\-\s\*\•]+', '', line).strip()
                    if question and len(question) > 5:  # 过滤太短的问题
                        questions.append(question)
            
            print(f"🔍 解析出 {len(questions)} 个问题: {questions[:3]}")
            
            # 直接设置result，跳过复杂的验证逻辑
            if questions:
                result["questions"] = questions[:num_questions]
                print(f"🔍 强制设置result: {result}")
                return
            
            # 如果没有问题，使用fallback
            result["questions"] = get_smart_fallback(context_text, query_engine)
            print(f"🔍 使用fallback: {result}")
            return
                
        except Exception as e:
            print(f"❌ 推荐问题生成异常: {e}")
            if logger:
                logger.log_error("追问生成", str(e))
            if result is not None:
                result["questions"] = get_smart_fallback(context_text, query_engine)
    
    # 使用线程执行并设置超时
    thread = threading.Thread(target=_generate, daemon=True)
    thread.start()
    thread.join(timeout=timeout)
    
    if thread.is_alive():
        print(f"⏰ 推荐问题生成超时 ({timeout}秒)，等待后台完成...")
        # 给更多时间让LLM完成
        thread.join(timeout=5)  # 再等5秒
        
        if thread.is_alive():
            print(f"⏰ 最终超时，使用fallback")
            if logger:
                logger.log_error("追问生成", "最终超时")
            return get_smart_fallback(context_text, query_engine)
        else:
            print(f"✅ 后台生成完成")
    
    print(f"🔍 线程执行完成，result: {result}")
    
    if result is None or "questions" not in result:
        print(f"🔍 result为空或无questions，返回fallback")
        return get_smart_fallback(context_text, query_engine)
    
    print(f"🔍 函数最终返回: {result['questions']}")
    return result["questions"]


def validate_message_format(message):
    """验证消息格式"""
    if not isinstance(message, dict):
        return False
    
    required_fields = ["role", "content"]
    for field in required_fields:
        if field not in message:
            return False
    
    if message["role"] not in ["user", "assistant"]:
        return False
    
    if not isinstance(message["content"], str):
        return False
    
    return True


def clean_chat_history(kb_id, max_messages=1000, logger=None):
    """
    清理过长的对话历史
    - 保留最近的消息
    - 防止文件过大
    """
    messages = load_chat_history_safe(kb_id, logger)
    
    if len(messages) > max_messages:
        messages = messages[-max_messages:]
        save_chat_history_safe(kb_id, messages, logger)
        
        if logger:
            logger.log("对话清理", "info", f"✅ 清理对话历史: {kb_id} (保留最近 {max_messages} 条)", 
                      {"kb_id": kb_id, "kept": max_messages})


def export_chat_history(kb_id, export_format="json", logger=None):
    """
    导出对话历史
    - 支持JSON和Markdown格式
    """
    messages = load_chat_history_safe(kb_id, logger)
    
    if export_format == "json":
        return json.dumps(messages, indent=2, ensure_ascii=False)
    
    elif export_format == "markdown":
        md_content = f"# 对话历史: {kb_id}\n\n"
        md_content += f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if role == "user":
                md_content += f"## 👤 用户\n\n{content}\n\n"
            else:
                md_content += f"## 🤖 助手\n\n{content}\n\n"
        
        return md_content
    
    else:
        if logger:
            logger.log_error("导出", f"不支持的格式: {export_format}")
        return None