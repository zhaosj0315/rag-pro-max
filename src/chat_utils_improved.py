"""
改进的对话处理工具 - 稳定性优先
- 安全的流式输出
- 引用源验证
- 追问生成容错
- 对话历史保护
"""

import os
import json
import threading
import time
import re
from pathlib import Path
from collections import Counter
from llama_index.core import Settings
import re

HISTORY_DIR = "chat_histories"
Path(HISTORY_DIR).mkdir(parents=True, exist_ok=True)


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
        
        if result is None:
            result = {"questions": []}
        
        # 尝试从多个来源获取LLM
        llm = None
        
        # 1. 优先使用传入的LLM
        if llm_model:
            llm = llm_model
        
        # 2. 从Settings获取
        elif hasattr(Settings, 'llm') and Settings.llm:
            llm = Settings.llm
        
        # 3. 从query_engine获取
        elif query_engine and hasattr(query_engine, '_llm'):
            llm = query_engine._llm
        
        if not llm:
            result["questions"] = get_smart_fallback(context_text, query_engine)
            return
        

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
            
            
            try:
                resp = llm.complete(prompt)
                text = resp.text.strip()
            except Exception as e:
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
            
            
            # 直接设置result，跳过复杂的验证逻辑
            if questions:
                result["questions"] = questions[:num_questions]
                return
            
            # 如果没有问题，使用fallback
            result["questions"] = get_smart_fallback(context_text, query_engine)
            return
                
        except Exception as e:
            if logger:
                logger.log_error("追问生成", str(e))
            if result is not None:
                result["questions"] = get_smart_fallback(context_text, query_engine)
    
    # 使用线程执行并设置超时
    thread = threading.Thread(target=_generate, daemon=True)
    thread.start()
    thread.join(timeout=timeout)
    
    if thread.is_alive():
        # 给更多时间让LLM完成
        thread.join(timeout=5)  # 再等5秒
        
        if thread.is_alive():
            if logger:
                logger.log_error("追问生成", "最终超时")
            return get_smart_fallback(context_text, query_engine)
    
    
    if result is None or "questions" not in result:
        return get_smart_fallback(context_text, query_engine)
    
    return result["questions"]
    