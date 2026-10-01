import sys
import threading
import time
from rich.console import Console
from rich.panel import Panel
import config
from utils.logger import log_info, log_action, log_success, log_error, log_warning
from utils.failsafe import start_failsafe
from voice.tts import tts
from voice.listener import VoiceListener
from core.router import classify_intent
from core.agent import agent
from core.conversation import chat_manager

console = Console()

def handle_user_command(command: str):
    """Routes command to either desktop agent or conversational chat."""
    if not command or not command.strip():
        return

    intent = classify_intent(command)

    if intent == "ACTION":
        log_action(f"Маршрутизация: ДЕЙСТВИЕ НА ЭКРАНЕ -> '{command}'")
        tts.speak("Выполняю задачу, сэр.", wait=False)
        result = agent.run_task(command)
        tts.speak(f"Задача завершена: {result}", wait=False)
    else:
        log_info(f"Маршрутизация: РАЗГОВОР -> '{command}'")
        chat_manager.reply(command, voice_output=True)

def voice_listener_worker(listener: VoiceListener):
    listener.listen_continuous(handle_user_command)

def main():
    w, h = config.get_screen_resolution()
    banner = f"""[bold cyan]J.A.R.V.I.S. Desktop & Voice Agent[/bold cyan]
[dim]------------------------------------------------[/dim]
[green]Экран:[/green] {w}x{h} (DPI-aware)
[green]Модель разума:[/green] {config.MODEL_NAME}
[green]Модель синтеза речи:[/green] {config.TTS_MODEL} ({config.TTS_VOICE})
[green]Ключевые слова активации:[/green] {", ".join(config.WAKE_WORDS)}
[yellow]Аварийный стоп:[/yellow] [bold red]Ctrl + Alt + Q[/bold red]
[dim]------------------------------------------------[/dim]"""

    console.print(Panel(banner, border_style="cyan"))

    # Start emergency failsafe listener
    start_failsafe()

    # Audio greeting
    tts.speak("Системы инициализированы. Джарвис готов к работе, сэр.", wait=False)

    # Initialize voice listener
    listener = VoiceListener()

    # Prompt user for mode
    console.print("\n[bold yellow]Выберите режим работы:[/bold yellow]")
    console.print("  [1] Текстовый CLI (ввод команд с клавиатуры)")
    console.print("  [2] Полноценный Голосовой режим (микрофон + 'Привет, Джарвис')")
    console.print("  [3] Комбинированный режим (фоновый микрофон + консоль)")

    choice = input("\nВведите 1, 2 или 3 (по умолчанию 3): ").strip()
    if not choice:
        choice = "3"

    if choice in ("2", "3"):
        voice_thread = threading.Thread(target=voice_listener_worker, args=(listener,), daemon=True)
        voice_thread.start()
        log_info("Фоновый голосовой монитор активирован.")

    log_info("Система активна. Введите 'exit' или 'выход' для завершения.")

    try:
        while True:
            cmd = input("\n[Jarvis Prompt] > ").strip()
            if not cmd:
                continue
            if cmd.lower() in ("exit", "quit", "выход", "стоп"):
                break
            handle_user_command(cmd)
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()
        log_info("Завершение работы Джарвиса. До свидания, сэр.")

if __name__ == "__main__":
    main()
