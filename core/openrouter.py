import time
import json
import httpx
import config
from utils.logger import log_info, log_warning, log_error

COMPUTER_USE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "mouse_click",
            "description": "Клик мыши по точным координатам экрана (X, Y).",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X координата в пикселях (от 0 до ширины экрана)"},
                    "y": {"type": "integer", "description": "Y координата в пикселях (от 0 до высоты экрана)"},
                    "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"},
                    "double": {"type": "boolean", "default": False, "description": "Двойной клик"}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_drag",
            "description": "Перетаскивание курсора мыши (drag and drop) от начальной точки к конечной.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_x": {"type": "integer"},
                    "start_y": {"type": "integer"},
                    "end_x": {"type": "integer"},
                    "end_y": {"type": "integer"}
                },
                "required": ["start_x", "start_y", "end_x", "end_y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_scroll",
            "description": "Прокрутка колесика мыши (положительное число = вверх, отрицательное = вниз).",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "integer", "description": "Количество шагов скролла (например: -3 для скролла вниз)"}
                },
                "required": ["amount"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "keyboard_type",
            "description": "Ввод текстовой строки (поддерживает русский и английский текст).",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Текст для набора"}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "keyboard_hotkey",
            "description": "Нажатие комбинации клавиш (например: ['win', 'r'], ['ctrl', 'c'], ['enter'], ['alt', 'f4']).",
            "parameters": {
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Список клавиш для одновременного нажатия"
                    }
                },
                "required": ["keys"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wait",
            "description": "Пауза в секундах для ожидания загрузки страницы или программы.",
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {"type": "number", "default": 1.0}
                },
                "required": ["seconds"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "task_completed",
            "description": "Вызывается, когда поставленная пользователем задача полностью завершена.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "Краткий отчет о выполненном действии"}
                },
                "required": ["summary"]
            }
        }
    }
]

class OpenRouterClient:
    def __init__(self):
        self.api_key = config.OPENROUTER_API_KEY
        self.model = config.MODEL_NAME
        self.vision_model = config.VISION_MODEL_NAME
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def _post_with_retry(self, payload: dict, max_retries: int = 3) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/jarvis-assistant",
            "X-Title": "Jarvis Desktop Agent"
        }
        backoff = 2.0
        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=45.0) as client:
                    resp = client.post(self.base_url, headers=headers, json=payload)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 429:
                    log_warning(f"OpenRouter 429 rate limit. Waiting {backoff:.1f}s before retry ({attempt+1}/{max_retries})...")
                    time.sleep(backoff)
                    backoff *= 2.0
                else:
                    log_error(f"OpenRouter error {resp.status_code}: {resp.text}")
                    time.sleep(backoff)
            except Exception as e:
                log_error(f"HTTP request exception: {e}")
                time.sleep(backoff)
        return {}

    def chat(self, messages: list[dict], model: str = None) -> str:
        """Standard text chat completion (for Q&A, voice dialogue)."""
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": 0.7
        }
        res = self._post_with_retry(payload)
        if res and "choices" in res and len(res["choices"]) > 0:
            return res["choices"][0]["message"]["content"] or ""
        return ""

    def step_agent(self, messages: list[dict], model: str = None) -> tuple[str, list[dict]]:
        """
        Sends state and screen to model with tools enabled.
        Returns: (reasoning_text, list_of_tool_calls)
        """
        payload = {
            "model": model or self.vision_model,
            "messages": messages,
            "tools": COMPUTER_USE_TOOLS,
            "tool_choice": "auto",
            "temperature": 0.2
        }
        res = self._post_with_retry(payload)
        if not res or "choices" not in res or not res["choices"]:
            return "", []

        msg = res["choices"][0]["message"]
        content = msg.get("content") or ""
        tool_calls = msg.get("tool_calls") or []

        return content, tool_calls

# Global singleton
ai = OpenRouterClient()
