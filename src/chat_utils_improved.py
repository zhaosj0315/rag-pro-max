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


def generate_follow_up_questions_safe(context_text, num_questions=3, existing_questions=None, timeout=10, logger=None, query_engine=None):
    """
    安全的追问生成（带降级策略）
    - 包含降级逻辑
    - 超时控制
    - 线程隔离
    - 知识库内容验证（新增）
    """
    result = {"questions": []}
    
    # 降级问题库
    fallback_questions = [
        "能否详细解释一下这个概念？",
        "这个方案有什么优缺点？",
        "有没有相关的实际案例？",
        "这与常见做法有什么区别？",
        "如何处理其中可能出现的错误？"
    ]
    
    # 根据上下文调整降级问题
    if "如何" in context_text or "怎么" in context_text:
        fallback_questions.insert(0, "具体的操作步骤是什么？")
    if "原因" in context_text or "为什么" in context_text:
        fallback_questions.insert(0, "还有其他可能的原因吗？")
    if "代码" in context_text or "Python" in context_text:
        fallback_questions.insert(0, "能否提供更详细的代码示例？")
        
    fallback = fallback_questions[:num_questions]

    def _generate():
        if not hasattr(Settings, 'llm') or not Settings.llm: 
            result["questions"] = fallback
            return

        try:
            # 减少上下文长度，提高速度
            short_context = context_text[-2000:] 
            
            # 排除已问过的问题
            existing_str = "\n".join(existing_questions) if existing_questions else ""
            
            # 🆕 尝试从知识库获取相关主题
            kb_topics = ""
            if query_engine:
                try:
                    # 提取关键词查询知识库
                    keywords = _extract_keywords(short_context)
                    if keywords:
                        kb_query = " ".join(keywords[:3])  # 使用前3个关键词
                        kb_response = query_engine.query(kb_query)
                        if kb_response and hasattr(kb_response, 'source_nodes'):
                            # 获取相关文档的标题或摘要
                            topics = []
                            for node in kb_response.source_nodes[:2]:  # 只取前2个
                                if hasattr(node, 'metadata') and 'file_name' in node.metadata:
                                    topics.append(node.metadata['file_name'])
                            if topics:
                                kb_topics = f"\n知识库相关主题：{', '.join(topics)}"
                except:
                    pass  # 静默失败，不影响主流程
            
            prompt = (
                f"基于以下回答，提出 {num_questions * 2} 个简短的追问问题。\n"
                f"要求：\n1. 只需要问题，不要序号\n2. 简短（15字以内）\n3. 有启发性\n"
                f"4. 结合知识库内容，提出用户可能感兴趣的相关问题\n"
                f"{'避免：' + existing_str if existing_str else ''}\n"
                f"{kb_topics}\n\n"
                f"内容：\n{short_context}"
            )
            
            resp = Settings.llm.complete(prompt)
            text = resp.text.strip()
            
            questions = [re.sub(r'^[\\d\\.\\-\\s]+', '', q).strip() for q in text.split('\n') if q.strip()]
            
            # 验证问题是否能在知识库中找到内容
            if query_engine and questions:
                valid_questions = []
                for q in questions[:num_questions * 2]:  # 多生成一些备选
                    try:
                        # 快速检索验证
                        retriever = query_engine.retriever
                        nodes = retriever.retrieve(q)
                        # 检查是否有高相关度的结果
                        if nodes and len(nodes) > 0 and nodes[0].score > 0.3:
                            valid_questions.append(q)
                            if len(valid_questions) >= num_questions:
                                break
                    except:
                        continue
                
                if valid_questions:
                    result["questions"] = valid_questions[:num_questions]
                else:
                    result["questions"] = fallback
            elif not questions:
                result["questions"] = fallback
            else:
                result["questions"] = questions[:num_questions]
                
        except Exception as e:
            if logger:
                logger.log_error("追问生成", str(e))
            result["questions"] = fallback
    
    # 使用线程执行并设置超时
    thread = threading.Thread(target=_generate, daemon=True)
    thread.start()
    thread.join(timeout=timeout)
    
    if thread.is_alive():
        if logger:
            logger.log_error("追问生成", "超时")
        return fallback
    
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