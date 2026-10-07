import os
import re
import threading
from backend.config import GROQ_API_KEY, VISION_MODELS, TEXT_MODELS

_rotation_lock = threading.Lock()
_next_key_index = 0


def _get_api_keys():
    """Return configured Groq keys, accepting a comma-separated pool or legacy key."""
    configured = os.environ.get("GROQ_API_KEYS", "")
    keys = [key.strip() for key in configured.split(",") if key.strip()]
    legacy_key = os.environ.get("GROQ_API_KEY") or GROQ_API_KEY
    if legacy_key and legacy_key not in keys:
        keys.append(legacy_key)
    if not keys:
        raise ValueError(
            "No Groq API keys configured. Set GROQ_API_KEYS (comma-separated) "
            "or GROQ_API_KEY in the environment or .env file."
        )
    return keys


def _get_groq_clients_in_rotation_order():
    global _next_key_index
    keys = _get_api_keys()
    with _rotation_lock:
        start = _next_key_index % len(keys)
        _next_key_index = (start + 1) % len(keys)
    try:
        from groq import Groq
    except ImportError as e:
        raise ImportError("The 'groq' package is not installed. Install it via 'pip install groq'.") from e
    return [Groq(api_key=keys[(start + offset) % len(keys)]) for offset in range(len(keys))]


def create_groq_completion(**kwargs):
    """Round-robin requests across keys; retry another key on quota/auth/server errors."""
    last_error = None
    for client in _get_groq_clients_in_rotation_order():
        try:
            return client.chat.completions.create(**kwargs)
        except Exception as error:
            status = getattr(error, "status_code", None)
            if status not in (401, 403, 429) and not (status and status >= 500):
                raise
            last_error = error
    raise last_error

def clean_thinking_tags(text: str) -> str:
    """Removes model thinking tokens (e.g. <think>...</think>) from output."""
    if not text:
        return ""
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return cleaned.strip()

def get_groq_client():
    """Return the next Groq client in round-robin order (legacy callers)."""
    return _get_groq_clients_in_rotation_order()[0]
