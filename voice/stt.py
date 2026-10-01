import os
import io
import numpy as np
from faster_whisper import WhisperModel
from utils.logger import log_info, log_error

class SpeechToText:
    def __init__(self, model_size: str = "base"):
        log_info(f"Loading Whisper STT model ('{model_size}')...")
        # CPU with int8 quantization is blazing fast and lightweight
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        log_info("Whisper STT model loaded successfully.")

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Transcribes audio array (float32 mono at 16kHz) to text.
        """
        try:
            # faster-whisper accepts float32 numpy array normalized between -1.0 and 1.0
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)

            segments, info = self.model.transcribe(
                audio_data,
                beam_size=5,
                language="ru",
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )

            text_chunks = [seg.text.strip() for seg in segments if seg.text.strip()]
            full_text = " ".join(text_chunks).strip()
            return full_text
        except Exception as e:
            log_error(f"STT transcription error: {e}")
            return ""

# Lazy loader
_stt_instance = None

def get_stt() -> SpeechToText:
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = SpeechToText()
    return _stt_instance
