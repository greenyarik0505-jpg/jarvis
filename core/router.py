import json
import re
from core.openrouter import ai
from core.prompts import ROUTER_SYSTEM_PROMPT
from utils.logger import log_info

ACTION_KEYWORDS = [
    "открой", "закрой", "нажми", "кликни", "напечатай", "введи", "сверни", "разверни",
    "сохрани", "найди", "включи", "выключи", "перейди", "скопируй", "вставь",
    "open", "close", "click", "type", "press", "search", "minimize", "maximize"
]

CHAT_KEYWORDS = [
    "привет", "здравствуй", "как дела", "кто ты", "что ты умеешь", "расскажи",
    "почему", "зачем", "анекдот", "шутк", "спасибо", "пока", "hello", "hi", "how are you"
]

def classify_intent(query: str) -> str:
    """
    Determines if user command is 'ACTION' (computer use) or 'CHAT' (voice dialog).
    Returns 'ACTION' or 'CHAT'.
    """
    lower = query.lower().strip()

    # Fast heuristics
    has_action = any(k in lower for k in ACTION_KEYWORDS)
    has_chat = any(k in lower for k in CHAT_KEYWORDS)

    if has_action and not has_chat:
        return "ACTION"
    if has_chat and not has_action:
        return "CHAT"

    # LLM classification for nuanced inputs
    try:
        messages = [
            {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
            {"role": "user", "content": f"Команда: {query}"}
        ]
        resp = ai.chat(messages)
        if "ACTION" in resp.upper():
            return "ACTION"
        return "CHAT"
    except Exception:
        # Default to CHAT if ambiguous
        return "CHAT"
