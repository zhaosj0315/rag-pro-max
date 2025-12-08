import os
import json
from datetime import datetime
import time

LOG_DIR = "app_logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

class Logger:
    def __init__(self):
        self.log_file = os.path.join(LOG_DIR, f"log_{datetime.now().strftime('%Y%m%d')}.jsonl")
        self.timers = {}  # 记录各阶段开始时间
        self._cleanup_old_logs()
    
    def _cleanup_old_logs(self, days=30):
        """清理旧日志文件"""
        try:
            import glob
            from datetime import timedelta
            
            cutoff = datetime.now() - timedelta(days=days)
            for log_file in glob.glob(os.path.join(LOG_DIR, 'log_*.jsonl')):
                try:
                    # 从文件名提取日期 log_20251201.jsonl
                    filename = os.path.basename(log_file)
                    date_str = filename.split('_')[1].split('.')[0]
                    log_date = datetime.strptime(date_str, '%Y%m%d')
                    
                    if log_date < cutoff:
                        os.remove(log_file)
                        print(f"🗑️ 已自动清理旧日志: {filename}")
                except Exception:
                    continue
        except Exception as e:
            print(f"⚠️ 日志清理失败: {e}")
    
    def log(self, stage, status, message, details=None):
        """记录日志到文件和终端"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "status": status,
            "message": message,
            "details": details or {}
        }
        # 写入文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        # 输出到终端（简化格式）
        print(message)
    
    def start_timer(self, key):
        """开始计时"""
        self.timers[key] = time.time()
    
    def get_elapsed(self, key):
        """获取耗时（秒）"""
        if key in self.timers:
            return round(time.time() - self.timers[key], 2)
        return 0
    
    # 模型加载
    def log_model_loading(self, provider, model_name, status, error=None):
        if status == 'loading':
            self.start_timer(f"model_{provider}")
            msg = f"📥 正在加载{provider}模型: {model_name}"
        else:
            elapsed = self.get_elapsed(f"model_{provider}")
            msg = f"✅ 已加载{provider}模型: {model_name} ({elapsed}s)"
        self.log("模型加载", status, msg, {"provider": provider, "model": model_name, "error": error, "elapsed": self.get_elapsed(f"model_{provider}")})
    
    # 知识库处理
    def log_kb_start(self, kb_name=None):
        self.start_timer(f"kb_{kb_name}")
        msg = f"🚀 开始处理知识库{': ' + kb_name if kb_name else ''}"
        self.log("知识库处理", "start", msg, {"kb_name": kb_name})
    
    def log_kb_complete(self, kb_name=None, doc_count=0):
        elapsed = self.get_elapsed(f"kb_{kb_name}")
        msg = f"✅ 知识库处理完成: {kb_name} ({doc_count} 个文档, 耗时 {elapsed}s)"
        self.log("知识库处理", "complete", msg, {"kb_name": kb_name, "doc_count": doc_count, "elapsed": elapsed})
    
    def log_kb_load_index(self, kb_name):
        self.log("知识库处理", "loading", f"📂 加载现有索引: {kb_name}", {"kb_name": kb_name})
    
    def log_kb_scan_path(self, path, kb_name=None):
        self.log("知识库处理", "scanning", f"📄 扫描路径: {path}", {"path": path, "kb_name": kb_name})
    
    def log_kb_read_success(self, doc_count, file_count=0, kb_name=None):
        self.log("知识库处理", "success", f"✅ 读取成功: {file_count} 个文件，{doc_count} 个文档片段", 
                {"doc_count": doc_count, "file_count": file_count, "kb_name": kb_name})
    
    def log_kb_manifest(self, file_count, kb_name=None):
        self.log("知识库处理", "info", f"📋 构建文件清单，共 {file_count} 个文件", 
                {"file_count": file_count, "kb_name": kb_name})
    
    def log_kb_parse_complete(self, valid_count=0, kb_name=None):
        self.log("知识库处理", "success", f"✅ 解析完成: {valid_count} 个有效片段", 
                {"valid_count": valid_count, "kb_name": kb_name})
    
    def log_kb_mode(self, mode, kb_name=None):
        icon = "➕" if mode == "append" else "⚡️"
        msg = f"{icon} {'追加模式' if mode == 'append' else '新建模式'}"
        if kb_name:
            msg += f" [知识库: {kb_name}]"
        self.log("知识库处理", "info", msg, {"mode": mode, "kb_name": kb_name})
    
    def log_kb_persist(self, status, kb_name=None):
        msg = f"{'💾' if status == 'persisting' else '✅'} {'持久化存储' if status == 'persisting' else '存储完成'}"
        if kb_name and status == 'success':
            msg += f" [知识库: {kb_name}]"
        self.log("知识库处理", status, msg, {"kb_name": kb_name})
    
    # 知识库挂载
    def log_kb_mount_start(self, kb_name):
        self.start_timer(f"mount_{kb_name}")
        self.log("知识库挂载", "mounting", f"📚 正在挂载知识库: {kb_name}", {"kb_name": kb_name})
    
    def log_kb_mount_success(self, kb_name):
        elapsed = self.get_elapsed(f"mount_{kb_name}")
        self.log("知识库挂载", "success", f"✅ 知识库挂载成功: {kb_name} ({elapsed}s)", 
                {"kb_name": kb_name, "elapsed": elapsed})
    
    def log_kb_mount_error(self, kb_name, error):
        self.log("知识库挂载", "error", f"❌ 知识库挂载失败: {kb_name}", {"kb_name": kb_name, "error": str(error)})
    
    # 查询对话
    def log_user_question(self, question, kb_name=None):
        self.start_timer(f"query_{kb_name}")
        msg = f"💬 用户提问: {question}"
        if kb_name:
            msg += f" [知识库: {kb_name}]"
        self.log("查询对话", "question", msg, {"question": question, "kb_name": kb_name})
    
    def log_retrieval_start(self, kb_name=None):
        msg = f"🔍 正在检索知识库{': ' + kb_name if kb_name else ''}..."
        self.log("查询对话", "retrieving", msg, {"kb_name": kb_name})
    
    def log_retrieval_result(self, doc_count, kb_name=None):
        msg = f"📚 找到 {doc_count} 个相关文档片段"
        if kb_name:
            msg += f" [知识库: {kb_name}]"
        self.log("查询对话", "success", msg, {"doc_count": doc_count, "kb_name": kb_name})
    
    def log_answer_complete(self, kb_name=None, model=None, tokens=None, prompt_tokens=None, completion_tokens=None):
        elapsed = self.get_elapsed(f"query_{kb_name}")
        msg = f"✅ 回答生成完成 ({elapsed}s)"
        details = {"elapsed": elapsed}
        if kb_name:
            msg += f" [知识库: {kb_name}]"
            details["kb_name"] = kb_name
        if model:
            msg += f" [模型: {model}]"
            details["model"] = model
        if tokens:
            tokens_per_sec = tokens / elapsed if elapsed > 0 else 0
            msg += f" [tokens: {tokens} @ {tokens_per_sec:.1f}t/s]"
            details["tokens"] = tokens
            details["tokens_per_sec"] = round(tokens_per_sec, 1)
        if prompt_tokens is not None and completion_tokens is not None:
            msg += f" [in: {prompt_tokens} | out: {completion_tokens}]"
            details["prompt_tokens"] = prompt_tokens
            details["completion_tokens"] = completion_tokens
        self.log("查询对话", "success", msg, details)
    
    # 文件操作
    def log_file_upload(self, filename, status, error=None):
        msg = f"{'📤' if status == 'uploading' else '✅'} {'正在上传' if status == 'uploading' else '上传完成'}: {filename}"
        self.log("文件操作", status, msg, {"filename": filename, "error": error})
    
    def log_file_delete(self, filename):
        self.log("文件操作", "delete", f"🗑️ 删除文件: {filename}", {"filename": filename})
    
    # 配置操作
    def log_config_change(self, config_type, changes):
        self.log("配置操作", "update", f"⚙️ 更新{config_type}配置", {"config_type": config_type, "changes": changes})
    
    # 错误日志
    def log_error(self, stage, error, context=None):
        msg = f"❌ 错误: {str(error)[:200]}"
        details = {"error": str(error), "context": context}
        self.log(stage, "error", msg, details)

logger = Logger()
