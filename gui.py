import os
import sys
import threading
import time
import webview
import config
from voice.tts import tts
from voice.listener import VoiceListener
from voice.meeting_listener import meeting_listener
from core.router import classify_intent
from core.agent import agent
from core.conversation import chat_manager
from core.zoom import zoom
import utils.failsafe as failsafe
from utils.logger import log_info, log_action, log_success, log_error

class JarvisBridge:
    def __init__(self):
        self._window = None
        self.voice_enabled = True
        self.listener = None
        self.voice_thread = None

    def set_window(self, win):
        self._window = win

    def call_js(self, js_code: str):
        if self._window:
            try:
                self._window.evaluate_js(js_code)
            except Exception:
                pass

    def send_command(self, command: str) -> str:
        """Called from UI text input."""
        threading.Thread(target=self._process_command, args=(command,), daemon=True).start()
        return "OK"

    def _process_command(self, command: str):
        if not command or not command.strip():
            return

        lower = command.lower()

        # Check Zoom commands
        if "зум" in lower or "zoom" in lower:
            if any(w in lower for w in ("выйди", "покинь", "leave")):
                self.leave_zoom()
                return
            elif any(w in lower for w in ("зайди", "подключись", "войди", "join")):
                self.join_zoom(command)
                return

        intent = classify_intent(command)
        if intent == "ACTION":
            self.call_js("window.jarvisAPI.setState('EXECUTING')")
            self.call_js(f"window.jarvisAPI.onAction('Выполнение системного действия: {command}')")
            tts.speak("Выполняю задачу, сэр.", wait=False)
            result = agent.run_task(command)
            self.call_js(f"window.jarvisAPI.onJarvisReply('Задача завершена: {result}')")
            tts.speak(f"Задача завершена: {result}", wait=False)
        else:
            self.call_js("window.jarvisAPI.setState('SPEAKING')")
            reply = chat_manager.reply(command, voice_output=True)
            escaped = reply.replace("'", "\\'").replace("\n", " ")
            self.call_js(f"window.jarvisAPI.onJarvisReply('{escaped}')")

    def join_zoom(self, link: str) -> bool:
        self.call_js("window.jarvisAPI.setState('EXECUTING')")
        ok = zoom.join_meeting(link)
        if ok:
            meeting_listener.start()
            self.call_js("window.jarvisAPI.setState('ONLINE')")
            return True
        self.call_js("window.jarvisAPI.setState('ONLINE')")
        return False

    def leave_zoom(self):
        meeting_listener.stop()
        zoom.leave_meeting()

    def toggle_zoom_mute(self):
        zoom.unmute()

    def set_voice_enabled(self, enabled: bool):
        self.voice_enabled = enabled
        log_info(f"Голосовой ввод: {'ВКЛ' if enabled else 'ВЫКЛ'}")

    def emergency_stop(self):
        failsafe.request_stop()
        self.call_js("window.jarvisAPI.setState('ONLINE')")

    def on_voice_command(self, cmd: str):
        if not self.voice_enabled:
            return
        escaped = cmd.replace("'", "\\'")
        self.call_js(f"window.jarvisAPI.onUserSpeech('{escaped}')")
        self._process_command(cmd)

bridge = JarvisBridge()

def start_voice_loop():
    bridge.listener = VoiceListener()
    bridge.listener.listen_continuous(bridge.on_voice_command)

def main():
    # Start emergency kill switch
    failsafe.start_failsafe()

    # Start background voice listener thread
    voice_t = threading.Thread(target=start_voice_loop, daemon=True)
    voice_t.start()

    # Initial audio greeting
    tts.speak("Системы инициализированы. Джарвис готов к работе, сэр.", wait=False)

    ui_path = os.path.join(config.BASE_DIR, "ui", "index.html")

    window = webview.create_window(
        title="J.A.R.V.I.S. Desktop System",
        url=ui_path,
        js_api=bridge,
        width=1080,
        height=720,
        min_size=(900, 600),
        background_color="#030811"
    )
    bridge.set_window(window)

    webview.start(debug=False)

if __name__ == "__main__":
    main()
