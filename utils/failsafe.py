import threading
from pynput import keyboard
from utils.logger import log_warning, log_error

_stop_event = threading.Event()
_listener = None

def _on_emergency_stop():
    log_error("Emergency Stop triggered (Ctrl+Alt+Q)! Aborting agent execution...")
    _stop_event.set()

def start_failsafe():
    """Starts the background hotkey listener for emergency kill-switch."""
    global _listener
    if _listener is not None and _listener.is_alive():
        return

    _stop_event.clear()
    hotkey = keyboard.GlobalHotKeys({
        '<ctrl>+<alt>+q': _on_emergency_stop
    })
    hotkey.daemon = True
    hotkey.start()
    _listener = hotkey

def is_stopped() -> bool:
    """Returns True if emergency stop was triggered."""
    return _stop_event.is_set()

def request_stop():
    """Manually signals the agent to stop."""
    _stop_event.set()

def reset():
    """Resets the stop event for new tasks."""
    _stop_event.clear()
