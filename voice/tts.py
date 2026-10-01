import os
import wave
import threading
import winsound
from pathlib import Path
import httpx
import numpy as np
import sounddevice as sd
import config
from utils.logger import log_speech, log_error, log_warning, log_info

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

        # Cache device indices
        self.zoom_dev_idx = None
        self.user_dev_idx = None
        self._find_devices()

    def _find_devices(self):
        try:
            for idx, dev in enumerate(sd.query_devices()):
                if dev['max_output_channels'] > 0:
                    name = dev['name']
                    if config.ZOOM_VIRTUAL_LINE and config.ZOOM_VIRTUAL_LINE.lower() in name.lower() and self.zoom_dev_idx is None:
                        self.zoom_dev_idx = idx
                    if config.USER_HEADPHONES and config.USER_HEADPHONES.lower() in name.lower() and self.user_dev_idx is None:
                        self.user_dev_idx = idx
            log_info(f"Аудио-маршрутизация: Zoom Virtual Line = {self.zoom_dev_idx}, Наушники = {self.user_dev_idx}")
        except Exception as e:
            log_warning(f"Ошибка поиска аудио-устройств: {e}")

    def _save_pcm_as_wav(self, pcm_data: bytes, wav_path: Path):
        with wave.open(str(wav_path), "wb") as wav_out:
            wav_out.setnchannels(1)
            wav_out.setsampwidth(2)
            wav_out.setframerate(self.sample_rate)
            wav_out.writeframes(pcm_data)

    def _play_dual(self, pcm_data: bytes):
        """Plays audio simultaneously to Virtual Line (Zoom mic) and User Headphones."""
        audio_arr = np.frombuffer(pcm_data, dtype=np.int16).astype(np.float32) / 32768.0

        target_devices = []
        if self.zoom_dev_idx is not None:
            target_devices.append(self.zoom_dev_idx)
        if config.DUAL_TTS_OUTPUT and self.user_dev_idx is not None and self.user_dev_idx not in target_devices:
            target_devices.append(self.user_dev_idx)

        if not target_devices:
            # Fallback to default Windows sound
            self._save_pcm_as_wav(pcm_data, self.wav_file)
            winsound.PlaySound(str(self.wav_file), winsound.SND_FILENAME)
            return

        try:
            # Open streams to target devices and write audio
            streams = [
                sd.OutputStream(device=dev, samplerate=self.sample_rate, channels=1)
                for dev in target_devices
            ]
            for s in streams:
                s.start()

            # Stream chunks for smooth simultaneous playback
            chunk_size = 1024
            for i in range(0, len(audio_arr), chunk_size):
                chunk = audio_arr[i:i+chunk_size]
                for s in streams:
                    s.write(chunk)

            for s in streams:
                s.stop()
                s.close()

        except Exception as e:
            log_warning(f"Dual playback failed: {e}. Fallback to winsound.")
            self._save_pcm_as_wav(pcm_data, self.wav_file)
            winsound.PlaySound(str(self.wav_file), winsound.SND_FILENAME)

    def speak(self, text: str, wait: bool = True):
        """Synthesizes speech and outputs to Zoom and User headphones."""
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
                        self._play_dual(resp.content)
                    else:
                        log_warning(f"TTS API status {resp.status_code}: {resp.text}")
                except Exception as e:
                    log_error(f"TTS speech failed: {e}")

        if wait:
            _worker()
        else:
            t = threading.Thread(target=_worker, daemon=True)
            t.start()

# Global singleton
tts = TextToSpeech()
