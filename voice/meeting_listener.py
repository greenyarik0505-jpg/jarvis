import time
import threading
import numpy as np
import soundcard as sc
from voice.stt import get_stt
from voice.tts import tts
from core.openrouter import ai
from devices.controller import controller
from utils.logger import log_info, log_speech, log_error, log_action
import config

ZOOM_MEETING_PROMPT = """Ты — Jarvis, интеллектуальный ассистент, подключенный к конференции Zoom.
Ты слышишь реплики других участников встречи.
Твоя цель:
- Отвечать четко, вежливо и кратко (1-3 предложения), чтобы не занимать эфир.
- Помогать участникам встречи с фактами, резюмированием, расчетами и ответами на вопросы.
- Обращаться к участникам нейтрально и профессионально.
"""

class MeetingListener:
    def __init__(self, sample_rate: int = 16000, energy_threshold: float = 0.02):
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        self._stop_event = threading.Event()
        self.is_running = False
        self.auto_unmute = True # Press Alt+A before speaking and mute after

    def _listen_loop(self):
        log_info("Активирован аудио-перехват участников конференции Zoom (WASAPI Loopback)...")
        stt = get_stt()

        speaker = sc.default_speaker()
        loopback_mic = sc.get_microphone(id=str(speaker.id), include_loopback=True)

        chunk_frames = int(self.sample_rate * 0.1) # 100ms
        recorded_chunks = []
        silence_count = 0
        speech_active = False

        with loopback_mic.recorder(samplerate=self.sample_rate) as recorder:
            while not self._stop_event.is_set():
                try:
                    data = recorder.record(numframes=chunk_frames)
                    # Convert to mono float32
                    mono_data = np.mean(data, axis=1).astype(np.float32)
                    energy = np.sqrt(np.mean(mono_data**2))

                    if energy > self.energy_threshold:
                        speech_active = True
                        silence_count = 0
                        recorded_chunks.append(mono_data)
                    elif speech_active:
                        silence_count += 1
                        recorded_chunks.append(mono_data)

                        # ~0.9s of silence after speech -> finish phrase
                        if silence_count >= 9:
                            full_audio = np.concatenate(recorded_chunks, axis=0)
                            recorded_chunks = []
                            speech_active = False
                            silence_count = 0

                            # Process participant speech
                            phrase = stt.transcribe(full_audio)
                            if phrase and len(phrase.strip()) > 2:
                                self._handle_participant_phrase(phrase.strip())

                except Exception as e:
                    time.sleep(0.2)

    def _handle_participant_phrase(self, text: str):
        log_speech("Zoom Участник", text)

        lower = text.lower()
        # React if participants mention Jarvis or ask a direct question
        needs_reply = any(w in lower for w in config.WAKE_WORDS) or "скажи" in lower or "ответь" in lower

        if needs_reply:
            log_action("Формирование ответа для участников Zoom...")
            messages = [
                {"role": "system", "content": ZOOM_MEETING_PROMPT},
                {"role": "user", "content": f"Реплика в конференции: {text}"}
            ]
            reply_text = ai.chat(messages)
            if not reply_text:
                reply_text = "Я на связи и готов помочь в ходе конференции."

            log_speech("Jarvis (В Zoom)", reply_text)

            if self.auto_unmute:
                # Unmute in Zoom (Alt+A)
                controller.hotkey("alt", "a")
                time.sleep(0.2)

            # Speak into meeting
            tts.speak(reply_text, wait=True)

            if self.auto_unmute:
                # Mute back (Alt+A)
                time.sleep(0.2)
                controller.hotkey("alt", "a")

    def start(self):
        if self.is_running:
            return
        self._stop_event.clear()
        self.is_running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self.is_running = False

# Global singleton
meeting_listener = MeetingListener()
