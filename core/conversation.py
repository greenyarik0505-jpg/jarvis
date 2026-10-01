from core.openrouter import ai
from core.prompts import CONVERSATION_SYSTEM_PROMPT
from voice.tts import tts
from utils.logger import log_speech

class ConversationManager:
    def __init__(self):
        self.history = [
            {"role": "system", "content": CONVERSATION_SYSTEM_PROMPT}
        ]

    def reply(self, user_text: str, voice_output: bool = True) -> str:
        """Processes conversational input, generates response, and speaks it."""
        self.history.append({"role": "user", "content": user_text})

        # Keep last 10 messages for context
        if len(self.history) > 12:
            self.history = [self.history[0]] + self.history[-10:]

        answer = ai.chat(self.history)
        if not answer:
            answer = "Слушаю вас, сэр. Чем могу помочь?"

        self.history.append({"role": "assistant", "content": answer})

        if voice_output:
            tts.speak(answer, wait=False)

        return answer

# Global singleton
chat_manager = ConversationManager()
