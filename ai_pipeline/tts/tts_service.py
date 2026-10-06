import asyncio
from pathlib import Path
from typing import Dict

from backend.config import AUDIO_DIR
from ai_pipeline.languages import LANGUAGES


class TTSService:
    """Create accessible audio tracks with a natural female voice per language."""

    def synthesize_bilingual(self, text_en: str, text_hi: str, event_id: str) -> Dict[str, str]:
        """Backward-compatible English/Hindi helper used by older callers."""
        return self.synthesize_translations({"en": text_en, "hi": text_hi}, event_id)

    def synthesize_translations(self, texts: Dict[str, str], event_id: str) -> Dict[str, str]:
        audio_urls = {}
        for language_code, text in texts.items():
            language = LANGUAGES.get(language_code)
            if not language or not text:
                continue

            filename = f"{event_id}_{language_code}.mp3"
            output_path = AUDIO_DIR / filename
            if self.synthesize_text(text, output_path, language_code):
                audio_urls[f"audio_{language_code}"] = f"/storage/audio/{filename}"

        return audio_urls

    def synthesize_text(self, text: str, output_path: Path, language_code: str = "en") -> bool:
        language = LANGUAGES.get(language_code)
        if not language or not text:
            return False

        output_path = Path(output_path).resolve()
        voice = language["voice"]

        # Edge TTS exposes named neural voices, allowing female Indian voices by locale.
        if voice:
            try:
                import edge_tts

                async def save_with_edge_voice():
                    communicate = edge_tts.Communicate(text, voice, rate="-5%")
                    await communicate.save(str(output_path))

                asyncio.run(save_with_edge_voice())
                if output_path.is_file() and output_path.stat().st_size > 0:
                    return True
            except Exception as error:
                print(f"Edge TTS error ({language_code}, {voice}): {error}. Trying gTTS fallback...")

        # gTTS covers Punjabi, for which the current Edge voice catalog has no pa-IN voice,
        # and also provides a fallback if the neural voice service is temporarily unavailable.
        try:
            from gtts import gTTS

            options = {"tld": "co.in"} if language_code == "en" else {}
            gTTS(text=text, lang=language["tts_code"], **options).save(str(output_path))
            if output_path.is_file() and output_path.stat().st_size > 0:
                return True
        except Exception as error:
            print(f"gTTS error ({language_code}): {error}. Trying offline speech fallback...")

        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.save_to_file(text, str(output_path))
            engine.runAndWait()
            return output_path.is_file() and output_path.stat().st_size > 0
        except Exception as error:
            print(f"Offline TTS fallback error ({language_code}): {error}")
            return False
