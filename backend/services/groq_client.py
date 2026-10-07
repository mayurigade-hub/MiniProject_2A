import os
import re
from backend.config import GROQ_API_KEY, VISION_MODELS, TEXT_MODELS

def clean_thinking_tags(text: str) -> str:
    """Removes model thinking tokens (e.g. <think>...</think>) from output."""
    if not text:
        return ""
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return cleaned.strip()

def get_groq_client():
    """Retrieves Groq API client or raises ValueError if API key is missing."""
    api_key = os.environ.get("GROQ_API_KEY") or GROQ_API_KEY
    if not api_key:
        raise ValueError(
            "Error: GROQ_API_KEY environment variable is not set. "
            "Please export GROQ_API_KEY or set it in a .env file."
        )
    
    try:
        from groq import Groq
        return Groq(api_key=api_key)
    except ImportError:
        raise ImportError(
            "Error: 'groq' package is not installed. "
            "Install it via 'pip install groq'."
        )
