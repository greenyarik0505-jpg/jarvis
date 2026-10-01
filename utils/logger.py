import sys
try:
    from rich.console import Console
    from rich.theme import Theme
    custom_theme = Theme({
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "action": "bold magenta",
        "speech": "italic blue",
    })
    console = Console(theme=custom_theme)
except ImportError:
    class FallbackConsole:
        def print(self, *args, **kwargs):
            text = " ".join(str(a) for a in args)
            print(text)
    console = FallbackConsole()

def log_info(msg: str):
    console.print(f"[info][JARVIS][/info] {msg}")

def log_action(msg: str):
    console.print(f"[action][ACTION][/action] {msg}")

def log_speech(speaker: str, msg: str):
    console.print(f"[speech][{speaker}][/speech] {msg}")

def log_warning(msg: str):
    console.print(f"[warning][WARNING][/warning] {msg}")

def log_error(msg: str):
    console.print(f"[error][ERROR][/error] {msg}")

def log_success(msg: str):
    console.print(f"[success][SUCCESS][/success] {msg}")
