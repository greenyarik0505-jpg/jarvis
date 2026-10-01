import time
import json
import config
from devices.screen import screen
from devices.controller import controller
from core.openrouter import ai
from core.prompts import COMPUTER_USE_SYSTEM_PROMPT
from utils.logger import log_info, log_action, log_warning, log_success, log_error
import utils.failsafe as failsafe

class ComputerUseAgent:
    def __init__(self):
        self.max_steps = config.MAX_STEPS
        self.step_delay = config.STEP_DELAY

    def execute_tool(self, name: str, args: dict) -> str:
        """Executes a single tool call through the system controller."""
        if name == "mouse_click":
            x = int(args.get("x", 0))
            y = int(args.get("y", 0))
            btn = args.get("button", "left")
            dbl = bool(args.get("double", False))
            controller.click(x, y, button=btn, double=dbl)
            return f"Клик по ({x}, {y}) выполнен."

        elif name == "mouse_drag":
            sx = int(args.get("start_x", 0))
            sy = int(args.get("start_y", 0))
            ex = int(args.get("end_x", 0))
            ey = int(args.get("end_y", 0))
            controller.drag(sx, sy, ex, ey)
            return f"Перетаскивание из ({sx}, {sy}) в ({ex}, {ey}) выполнено."

        elif name == "mouse_scroll":
            amt = int(args.get("amount", 0))
            controller.scroll(amt)
            return f"Скролл {amt} выполнен."

        elif name == "keyboard_type":
            txt = str(args.get("text", ""))
            controller.type_text(txt)
            return f"Текст '{txt}' напечатан."

        elif name == "keyboard_hotkey":
            keys = args.get("keys", [])
            if isinstance(keys, list):
                controller.hotkey(*keys)
                return f"Комбинация клавиш {keys} нажата."
            return "Неверный формат клавиш."

        elif name == "wait":
            sec = float(args.get("seconds", 1.0))
            log_action(f"Ожидание {sec} сек...")
            time.sleep(sec)
            return f"Ожидание {sec} сек завершено."

        elif name == "task_completed":
            summary = args.get("summary", "Задача выполнена.")
            log_success(f"Задача завершена: {summary}")
            return f"Завершено: {summary}"

        return f"Неизвестный инструмент: {name}"

    def run_task(self, task: str) -> str:
        """
        Executes an autonomous ReAct loop to complete the user's desktop task.
        """
        failsafe.reset()
        failsafe.start_failsafe()

        log_info(f"Старт выполнения задачи: '{task}'")
        res_w, res_h = config.get_screen_resolution()
        sys_prompt = COMPUTER_USE_SYSTEM_PROMPT.format(width=res_w, height=res_h)

        # Initial message history
        messages = [
            {"role": "system", "content": sys_prompt}
        ]

        step = 0
        while step < self.max_steps:
            if failsafe.is_stopped():
                log_error("Выполнение прервано пользователем (Failsafe)!")
                return "Прервано пользователем."

            step += 1
            log_info(f"--- Шаг {step}/{self.max_steps} ---")

            # 1. Capture current screen
            img_url, w, h = screen.capture_base64()

            # 2. Prepare user message with current screenshot
            if step == 1:
                user_content = [
                    {"type": "text", "text": f"Задача: {task}\nТекущий снимок экрана:"},
                    {"type": "image_url", "image_url": {"url": img_url}}
                ]
            else:
                user_content = [
                    {"type": "text", "text": "Текущее состояние экрана после предыдущего действия:"},
                    {"type": "image_url", "image_url": {"url": img_url}}
                ]

            messages.append({"role": "user", "content": user_content})

            # 3. Request action from OpenRouter model
            reasoning, tool_calls = ai.step_agent(messages)

            if reasoning:
                log_info(f"Мысли агента: {reasoning}")

            if not tool_calls:
                log_warning("Модель не вернула действий. Завершение шага.")
                # If model responded with just text
                break

            # 4. Execute tool calls
            task_done = False
            tool_outputs = []

            for tc in tool_calls:
                fn = tc.get("function", {})
                fn_name = fn.get("name", "")
                try:
                    args = json.loads(fn.get("arguments", "{}"))
                except Exception:
                    args = {}

                result = self.execute_tool(fn_name, args)
                tool_outputs.append({
                    "tool_call_id": tc.get("id", f"call_{step}"),
                    "role": "tool",
                    "name": fn_name,
                    "content": result
                })

                if fn_name == "task_completed":
                    task_done = True
                    break

            if task_done:
                return "Задача успешно выполнена!"

            # 5. Optimize context: remove heavy image from previous message to keep context light
            if len(messages) >= 2 and isinstance(messages[-1]["content"], list):
                messages[-1]["content"] = [{"type": "text", "text": f"[Снимок экрана шага {step} обработан]"}]

            # Append assistant message & tool outputs
            messages.append({
                "role": "assistant",
                "content": reasoning or "",
                "tool_calls": tool_calls
            })
            for out in tool_outputs:
                messages.append(out)

            time.sleep(self.step_delay)

        log_warning("Достигнут лимит шагов.")
        return "Лимит шагов исчерпан."

# Global singleton
agent = ComputerUseAgent()
