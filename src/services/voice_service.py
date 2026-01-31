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
        # [v9.9.3] 极致纯净模式：移除所有引导词，回归原生识别
        self.model_size = os.getenv("WHISPER_MODEL_SIZE", "small") 
        self.device = "cpu"
        
        self.logger.info(f"🎙️ VoiceService initialized (Target Model: {self.model_size})")

    def _load_model(self):
        if self._model is not None:
            return self._model
        
        if WhisperModel is None:
            raise ImportError("请先安装依赖: pip install faster-whisper")

        try:
            self.logger.info(f"📥 Loading Whisper model '{self.model_size}'...")
            start_time = time.time()
            
            # 使用 int8 量化，确保速度
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
            # [v9.9.3] 移除 initial_prompt，确保原样输出
            segments, info = model.transcribe(
                audio_file, 
                beam_size=5, 
                language="zh",
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
