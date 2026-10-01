import os
import ctypes
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# DPI Awareness for exact coordinate mapping on Windows
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per_Monitor_DPI_Aware
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# OpenRouter settings
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen/qwen3.8-27b:free")
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "qwen/qwen3.8-27b:free")

# Voice settings
TTS_MODEL = os.getenv("TTS_MODEL", "deepgram/flux-tts:free")
TTS_VOICE = os.getenv("TTS_VOICE", "flux-bruce-en")
WAKE_WORDS = [w.strip().lower() for w in os.getenv("WAKE_WORDS", "джарвис,jarvis,привет джарвис").split(",") if w.strip()]

# Audio Device Routing (HitPaw Virtual Line for Zoom + Realtek for User)
ZOOM_VIRTUAL_LINE = os.getenv("ZOOM_VIRTUAL_LINE", "HitPaw")
USER_HEADPHONES = os.getenv("USER_HEADPHONES", "Realtek")
USER_MICROPHONE = os.getenv("USER_MICROPHONE", "Realtek")
DUAL_TTS_OUTPUT = os.getenv("DUAL_TTS_OUTPUT", "true").lower() == "true"

# Agent & Vision parameters
SCREEN_SCALE = float(os.getenv("SCREEN_SCALE", "1.0"))
JPEG_QUALITY = int(os.getenv("JPEG_QUALITY", "80"))
MAX_STEPS = int(os.getenv("MAX_STEPS", "25"))
STEP_DELAY = float(os.getenv("STEP_DELAY", "0.8"))

def get_screen_resolution() -> tuple[int, int]:
    """Returns actual physical width and height of the primary screen in pixels."""
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
