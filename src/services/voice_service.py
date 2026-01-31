import os
import time
import logging
from functools import lru_cache
try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

class VoiceService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VoiceService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化语音服务，延迟加载模型"""
        self.logger = logging.getLogger(__name__)
        # [v9.9.2] 回退至 small 以保证毫秒级响应速度
        self.model_size = os.getenv("WHISPER_MODEL_SIZE", "small") 
        self.device = "cpu"
        # 预设专业术语提示词，引导模型正确识别
        self.initial_prompt = "这是一个关于 RAG Pro Max AI 知识库、数据分析、SQL、向量检索和人工智能的对话系统。请准确识别：知识库、RAG、数据库。"
        
        self.logger.info(f"🎙️ VoiceService initialized (Target Model: {self.model_size})")

    def _load_model(self):
        if self._model is not None:
            return self._model
        
        if WhisperModel is None:
            raise ImportError("请先安装依赖: pip install faster-whisper")

        try:
            self.logger.info(f"📥 Loading Whisper model '{self.model_size}'...")
            start_time = time.time()
            
            # 使用 int8 量化，速度极快
            self._model = WhisperModel(
                self.model_size, 
                device=self.device, 
                compute_type="int8", 
                download_root=os.path.join(os.getcwd(), "hf_cache", "whisper")
            )
            
            elapsed = time.time() - start_time
            self.logger.info(f"✅ Whisper model loaded in {elapsed:.2f}s")
            return self._model
        except Exception as e:
            self.logger.error(f"❌ Failed to load Whisper model: {e}")
            return None

    def transcribe(self, audio_file) -> str:
        """
        将音频文件流转录为文字
        :param audio_file: 文件对象 (BytesIO)
        :return: 转录后的文本
        """
        model = self._load_model()
        if not model:
            return ""

        try:
            # [v9.9.2 Optimization] 注入 initial_prompt 以提升 small 模型的专业词汇命中率
            segments, info = model.transcribe(
                audio_file, 
                beam_size=5, 
                language="zh",
                initial_prompt=self.initial_prompt, # 关键优化
                vad_filter=True 
            )
            
            text_segments = []
            for segment in segments:
                text_segments.append(segment.text)
            
            full_text = "".join(text_segments).strip()
            self.logger.info(f"🗣️ Transcribed: '{full_text}' (Prob: {info.language_probability:.2f})")
            return full_text
            
        except Exception as e:
            self.logger.error(f"❌ Transcription error: {e}")
            return ""

# 全局单例获取
def get_voice_service():
    return VoiceService()
