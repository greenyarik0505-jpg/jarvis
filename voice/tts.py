import os
import wave
import threading
import winsound
from pathlib import Path
import httpx
import config
from utils.logger import log_speech, log_error, log_warning

_audio_lock = threading.Lock()

class TextToSpeech:
    def __init__(self):
        self.api_key = config.OPENROUTER_API_KEY
        self.model = config.TTS_MODEL
        self.voice = config.TTS_VOICE
        self.sample_rate = 24000
        self.temp_dir = config.BASE_DIR / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.wav_file = self.temp_dir / "speech.wav"

    def _save_pcm_as_wav(self, pcm_data: bytes, wav_path: Path):
        """Wraps raw 16-bit mono 24kHz PCM from Deepgram Flux-TTS into a standard WAV file."""
        with wave.open(str(wav_path), "wb") as wav_out:
            wav_out.setnchannels(1)
            wav_out.setsampwidth(2)  # 16-bit = 2 bytes
            wav_out.setframerate(self.sample_rate)
            wav_out.writeframes(pcm_data)

    def speak(self, text: str, wait: bool = True):
        """Synthesizes text to speech using OpenRouter Deepgram Flux-TTS and plays audio."""
        if not text or not text.strip():
            return

        log_speech("Jarvis (Voice)", text)

        def _worker():
            with _audio_lock:
                try:
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "model": self.model,
                        "voice": self.voice,
                        "input": text
                    }
                    with httpx.Client(timeout=15.0) as client:
                        resp = client.post(
                            "https://openrouter.ai/api/v1/audio/speech",
                            headers=headers,
                            json=payload
                        )
                    if resp.status_code == 200:
                        self._save_pcm_as_wav(resp.content, self.wav_file)
                        # Play synchronously or asynchronously via Windows native sound subsystem
                        flags = winsound.SND_FILENAME
                        if not wait:
                            flags |= winsound.SND_ASYNC
                        winsound.PlaySound(str(self.wav_file), flags)
                    else:
                        log_warning(f"TTS API returned status {resp.status_code}: {resp.text}")
                except Exception as e:
                    log_error(f"TTS speech generation failed: {e}")

        if wait:
            _worker()
        else:
            t = threading.Thread(target=_worker, daemon=True)
            t.start()

# Global singleton
tts = TextToSpeech()
