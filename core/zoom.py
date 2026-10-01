import os
import re
import time
import urllib.parse
import subprocess
from utils.logger import log_info, log_action, log_warning, log_success
from devices.controller import controller
from voice.tts import tts

ZOOM_EXE_PATH = os.path.expandvars(r"%APPDATA%\Zoom\bin\Zoom.exe")

class ZoomController:
    def __init__(self):
        self.in_meeting = False
        self.current_meeting_id = None

    def parse_meeting_info(self, raw_input: str) -> tuple[str, str]:
        """
        Extracts (confno, pwd) from URL or plain text like:
        - 'https://us05web.zoom.us/j/5397107998?pwd=SGFwSG1CcURPbVlUd09kZjcySU15UT09'
        - 'зайди в зум https://zoom.us/j/1234567890?pwd=abc'
        - '5397107998 код SGFwSG1...'
        """
        raw = raw_input.strip()

        # 1. Search for any Zoom URL
        url_match = re.search(r"https?://[^\s<>\"\'\)]+", raw)
        if url_match:
            url_str = url_match.group(0)
            try:
                parsed = urllib.parse.urlparse(url_str)
                # Matches /j/5397107998 or /wc/join/5397107998
                path_match = re.search(r"/(?:j|join|wc/join)/(\d+)", parsed.path)
                if path_match:
                    confno = path_match.group(1)
                    qs = urllib.parse.parse_qs(parsed.query)
                    pwd = qs.get("pwd", [""])[0]
                    return confno, pwd
            except Exception:
                pass

        # 2. Check for explicit 9-11 digit conference ID
        numbers = re.findall(r"\d{9,11}", raw)
        if numbers:
            confno = numbers[0]
            pwd_match = re.search(r"(?:пароль|pwd|passcode|код)[:\s=]+([a-zA-Z0-9_\-=\.]+)", raw, re.IGNORECASE)
            pwd = pwd_match.group(1) if pwd_match else ""
            return confno, pwd

        # 3. Check for any sequence of numbers
        all_numbers = re.findall(r"\d+", raw)
        if all_numbers:
            combined = "".join(all_numbers[:3])
            if len(combined) in (9, 10, 11):
                confno = combined
            else:
                confno = all_numbers[0]
            pwd_match = re.search(r"(?:пароль|pwd|passcode|код)[:\s=]+([a-zA-Z0-9_\-=\.]+)", raw, re.IGNORECASE)
            pwd = pwd_match.group(1) if pwd_match else ""
            return confno, pwd

        return "", ""

    def join_meeting(self, meeting_input: str, name: str = "Jarvis AI", auto_audio: bool = True) -> bool:
        """
        Joins a Zoom meeting using zoommtg:// protocol or Zoom.exe directly.
        """
        confno, pwd = self.parse_meeting_info(meeting_input)
        if not confno:
            log_warning(f"Не удалось распознать ID конференции в строке: {meeting_input}")
            tts.speak("Не удалось определить номер конференции Zoom, сэр.", wait=False)
            return False

        log_action(f"Подключение к конференции Zoom ID: {confno} (Имя: {name})...")
        tts.speak(f"Подключаюсь к конференции Zoom {confno}, сэр.", wait=False)

        encoded_name = urllib.parse.quote(name)
        uri = f"zoommtg://zoom.us/join?action=join&confno={confno}&uname={encoded_name}"
        if pwd:
            uri += f"&pwd={pwd}"

        try:
            # Launch via Windows protocol handler
            os.startfile(uri)
            self.in_meeting = True
            self.current_meeting_id = confno
            log_success("Команда подключения Zoom отправлена.")

            if auto_audio:
                # Wait for Zoom window to load and connect audio
                log_info("Ожидание окна Zoom (4 сек)...")
                time.sleep(4.0)

                # Press Enter / Space to confirm 'Join with Computer Audio' dialog if it appears
                controller.press_key("enter")
                time.sleep(0.5)

            return True
        except Exception as e:
            log_warning(f"Ошибка вызова протокола zoommtg: {e}. Попытка запуска через Zoom.exe...")
            if os.path.exists(ZOOM_EXE_PATH):
                cmd = [ZOOM_EXE_PATH, f"--url={uri}"]
                subprocess.Popen(cmd)
                self.in_meeting = True
                return True
            return False

    def unmute(self):
        """Unmutes audio in Zoom meeting (Alt + A)."""
        log_action("Zoom: Включение микрофона (Alt+A)")
        controller.hotkey("alt", "a")

    def mute(self):
        """Mutes audio in Zoom meeting (Alt + A)."""
        log_action("Zoom: Выключение микрофона (Alt+A)")
        controller.hotkey("alt", "a")

    def toggle_video(self):
        """Toggles camera in Zoom (Alt + V)."""
        log_action("Zoom: Переключение камеры (Alt+V)")
        controller.hotkey("alt", "v")

    def leave_meeting(self):
        """Leaves the current Zoom meeting (Alt + Q -> Enter)."""
        log_action("Zoom: Выход из конференции")
        controller.hotkey("alt", "q")
        time.sleep(0.5)
        controller.press_key("enter")
        self.in_meeting = False
        self.current_meeting_id = None
        tts.speak("Я покинул конференцию Zoom, сэр.", wait=False)

# Global singleton
zoom = ZoomController()
