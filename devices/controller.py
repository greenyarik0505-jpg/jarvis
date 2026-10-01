import ctypes
import time
from ctypes import wintypes
import config
from utils.logger import log_action

# Win32 Constants
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_ABSOLUTE = 0x8000

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008

# C Structs
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong)
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong)
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD)
    ]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT)
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", _INPUT_UNION)
    ]

LPINPUT = ctypes.POINTER(INPUT)
SendInput = ctypes.windll.user32.SendInput
SendInput.argtypes = (wintypes.UINT, LPINPUT, ctypes.c_int)
SendInput.restype = wintypes.UINT

SetCursorPos = ctypes.windll.user32.SetCursorPos
SetCursorPos.argtypes = (ctypes.c_int, ctypes.c_int)
SetCursorPos.restype = wintypes.BOOL

VK_MAP = {
    "win": 0x5B,
    "super": 0x5B,
    "ctrl": 0x11,
    "control": 0x11,
    "alt": 0x12,
    "shift": 0x10,
    "enter": 0x0D,
    "return": 0x0D,
    "esc": 0x1B,
    "escape": 0x1B,
    "tab": 0x09,
    "backspace": 0x08,
    "space": 0x20,
    "del": 0x2E,
    "delete": 0x2E,
    "up": 0x26,
    "down": 0x28,
    "left": 0x25,
    "right": 0x27,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
    "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73, "f5": 0x74, "f6": 0x75,
    "f7": 0x76, "f8": 0x77, "f9": 0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B
}

class InputController:
    def __init__(self):
        self.screen_w, self.screen_h = config.get_screen_resolution()

    def move(self, x: int, y: int):
        SetCursorPos(int(x), int(y))

    def _mouse_event(self, flags: int, data: int = 0):
        inp = INPUT(type=INPUT_MOUSE)
        inp.u.mi.dx = 0
        inp.u.mi.dy = 0
        inp.u.mi.mouseData = data
        inp.u.mi.dwFlags = flags
        inp.u.mi.time = 0
        inp.u.mi.dwExtraInfo = 0
        SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def mouse_down(self, x: int = None, y: int = None, button: str = "left"):
        if x is not None and y is not None:
            self.move(x, y)
            time.sleep(0.02)
        flag = MOUSEEVENTF_LEFTDOWN if button == "left" else (MOUSEEVENTF_RIGHTDOWN if button == "right" else MOUSEEVENTF_MIDDLEDOWN)
        self._mouse_event(flag)

    def mouse_up(self, x: int = None, y: int = None, button: str = "left"):
        if x is not None and y is not None:
            self.move(x, y)
            time.sleep(0.02)
        flag = MOUSEEVENTF_LEFTUP if button == "left" else (MOUSEEVENTF_RIGHTUP if button == "right" else MOUSEEVENTF_MIDDLEUP)
        self._mouse_event(flag)

    def click(self, x: int, y: int, button: str = "left", double: bool = False):
        log_action(f"Click at ({x}, {y}) [button={button}, double={double}]")
        self.move(x, y)
        time.sleep(0.05)
        self.mouse_down(button=button)
        time.sleep(0.04)
        self.mouse_up(button=button)
        if double:
            time.sleep(0.08)
            self.mouse_down(button=button)
            time.sleep(0.04)
            self.mouse_up(button=button)

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, steps: int = 20, delay: float = 0.01):
        log_action(f"Drag from ({start_x}, {start_y}) to ({end_x}, {end_y})")
        self.move(start_x, start_y)
        time.sleep(0.05)
        self.mouse_down(button="left")
        time.sleep(0.05)
        for i in range(1, steps + 1):
            cur_x = int(start_x + (end_x - start_x) * (i / steps))
            cur_y = int(start_y + (end_y - start_y) * (i / steps))
            self.move(cur_x, cur_y)
            time.sleep(delay)
        time.sleep(0.05)
        self.mouse_up(button="left")

    def scroll(self, amount: int):
        """Scroll wheel: positive = up, negative = down. Amount in standard wheel clicks (e.g. 1, -1, 3, -3)."""
        log_action(f"Scroll amount: {amount}")
        wheel_delta = amount * 120
        self._mouse_event(MOUSEEVENTF_WHEEL, data=wheel_delta)

    def type_text(self, text: str, delay: float = 0.01):
        """Types unicode string accurately regardless of active Windows keyboard layout."""
        log_action(f"Typing text: '{text}'")
        for char in text:
            # Special case: enter
            if char == '\n':
                self.press_key("enter")
                continue

            char_code = ord(char)
            # Key down
            inp_down = INPUT(type=INPUT_KEYBOARD)
            inp_down.u.ki.wVk = 0
            inp_down.u.ki.wScan = char_code
            inp_down.u.ki.dwFlags = KEYEVENTF_UNICODE
            inp_down.u.ki.time = 0
            inp_down.u.ki.dwExtraInfo = 0

            # Key up
            inp_up = INPUT(type=INPUT_KEYBOARD)
            inp_up.u.ki.wVk = 0
            inp_up.u.ki.wScan = char_code
            inp_up.u.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
            inp_up.u.ki.time = 0
            inp_up.u.ki.dwExtraInfo = 0

            SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(INPUT))
            if delay > 0:
                time.sleep(delay)
            SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(INPUT))
            if delay > 0:
                time.sleep(delay)

    def _vk_from_name(self, key_name: str) -> int:
        k = key_name.lower().strip()
        if k in VK_MAP:
            return VK_MAP[k]
        if len(k) == 1:
            # A-Z, 0-9
            vk = ctypes.windll.user32.VkKeyScanW(ord(k)) & 0xFF
            if vk != 0:
                return vk
        return 0

    def press_key(self, key_name: str):
        vk = self._vk_from_name(key_name)
        if not vk:
            return
        inp_down = INPUT(type=INPUT_KEYBOARD)
        inp_down.u.ki.wVk = vk
        inp_down.u.ki.dwFlags = 0
        SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(INPUT))
        time.sleep(0.03)
        inp_up = INPUT(type=INPUT_KEYBOARD)
        inp_up.u.ki.wVk = vk
        inp_up.u.ki.dwFlags = KEYEVENTF_KEYUP
        SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(INPUT))

    def hotkey(self, *keys: str):
        """Presses and releases a combination of keys, e.g. hotkey('ctrl', 'c') or hotkey('win', 'r')."""
        log_action(f"Hotkey: {' + '.join(keys)}")
        vk_list = [self._vk_from_name(k) for k in keys if self._vk_from_name(k) != 0]
        # Press all in order
        for vk in vk_list:
            inp = INPUT(type=INPUT_KEYBOARD)
            inp.u.ki.wVk = vk
            inp.u.ki.dwFlags = 0
            SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
            time.sleep(0.02)
        time.sleep(0.05)
        # Release in reverse order
        for vk in reversed(vk_list):
            inp = INPUT(type=INPUT_KEYBOARD)
            inp.u.ki.wVk = vk
            inp.u.ki.dwFlags = KEYEVENTF_KEYUP
            SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
            time.sleep(0.02)

# Global singleton
controller = InputController()
