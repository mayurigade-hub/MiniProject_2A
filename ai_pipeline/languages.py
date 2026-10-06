"""Audio-description language and voice configuration."""


LANGUAGES = {
    "en": {"name": "English (India)", "tts_code": "en", "voice": "en-IN-NeerjaNeural"},
    "hi": {"name": "Hindi", "tts_code": "hi", "voice": "hi-IN-SwaraNeural"},
    "bn": {"name": "Bengali", "tts_code": "bn", "voice": "bn-IN-TanishaaNeural"},
    "gu": {"name": "Gujarati", "tts_code": "gu", "voice": "gu-IN-DhwaniNeural"},
    "kn": {"name": "Kannada", "tts_code": "kn", "voice": "kn-IN-SapnaNeural"},
    "ml": {"name": "Malayalam", "tts_code": "ml", "voice": "ml-IN-SobhanaNeural"},
    "mr": {"name": "Marathi", "tts_code": "mr", "voice": "mr-IN-AarohiNeural"},
    # Edge TTS does not currently list an Indian Punjabi voice; use gTTS for pa.
    "pa": {"name": "Punjabi", "tts_code": "pa", "voice": None},
    "ta": {"name": "Tamil", "tts_code": "ta", "voice": "ta-IN-PallaviNeural"},
    "te": {"name": "Telugu", "tts_code": "te", "voice": "te-IN-ShrutiNeural"},
    "ur": {"name": "Urdu", "tts_code": "ur", "voice": "ur-IN-GulNeural"},
}

LANGUAGE_CODES = tuple(LANGUAGES)
