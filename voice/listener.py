import time
import threading
import numpy as np
import sounddevice as sd
import config
from voice.stt import get_stt
from utils.logger import log_info, log_speech, log_error, log_warning

class VoiceListener:
    def __init__(self, sample_rate: int = 16000, energy_threshold: float = 0.015):
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        self.wake_words = config.WAKE_WORDS
        self.is_listening = False
        self._stop_event = threading.Event()
        self.mic_device_idx = self._find_user_mic()

    def _find_user_mic(self):
        try:
            for idx, dev in enumerate(sd.query_devices()):
                if dev['max_input_channels'] > 0:
                    name = dev['name']
                    if config.USER_MICROPHONE and config.USER_MICROPHONE.lower() in name.lower():
                        log_info(f"Микрофон пользователя найден: [{idx}] {name}")
                        return idx
        except Exception:
            pass
        return None

    def record_phrase(self, max_duration: float = 12.0, silence_timeout: float = 1.0) -> np.ndarray:
        """
        Records a single spoken phrase until silence is detected.
        Returns float32 audio numpy array.
        """
        chunk_size = int(self.sample_rate * 0.1) # 100ms chunks
        recorded_chunks = []
        silence_duration = 0.0
        speech_started = False
        start_time = time.time()

        with sd.InputStream(device=self.mic_device_idx, samplerate=self.sample_rate, channels=1, dtype='float32', blocksize=chunk_size) as stream:
            while not self._stop_event.is_set():
                chunk, overflowed = stream.read(chunk_size)
                energy = np.sqrt(np.mean(chunk**2))

                if energy > self.energy_threshold:
                    speech_started = True
                    silence_duration = 0.0
                    recorded_chunks.append(chunk)
                elif speech_started:
                    silence_duration += 0.1
                    recorded_chunks.append(chunk)
                    if silence_duration >= silence_timeout:
                        break
                
                # Timeout safeguard
                if time.time() - start_time > max_duration:
                    break

        if not recorded_chunks:
            return np.array([], dtype=np.float32)

        return np.concatenate(recorded_chunks, axis=0).flatten()

    def listen_continuous(self, on_command_callback):
        """
        Continuously listens for wake word or direct commands and calls on_command_callback(text).
        """
        stt = get_stt()
        self.is_listening = True
        log_info(f"Jarvis is listening for wake words ({', '.join(self.wake_words)})...")

        while not self._stop_event.is_set():
            try:
                audio = self.record_phrase()
                if len(audio) == 0:
                    continue

                text = stt.transcribe(audio)
                if not text:
                    continue

                lower_text = text.lower().strip()
                log_speech("User (Mic)", text)

                # Check for wake word
                wake_word_detected = False
                matched_word = ""
                for w in self.wake_words:
                    if w in lower_text:
                        wake_word_detected = True
                        matched_word = w
                        break

                if wake_word_detected:
                    # Strip wake word to get clean command
                    cmd = lower_text.replace(matched_word, "").strip(" ,.!?")
                    if not cmd:
                        cmd = "привет"  # User just said wake word
                    on_command_callback(cmd)
                else:
                    # If user just spoke a direct command in active interaction
                    pass

            except Exception as e:
                log_error(f"Listener error: {e}")
                time.sleep(0.5)

    def stop(self):
        self._stop_event.set()
        self.is_listening = False
