import re
from typing import Dict
from backend.services.groq_client import create_groq_completion, clean_thinking_tags
from backend.config import TEXT_MODELS
from ai_pipeline.explanation.prompts import ENGLISH_EXPLANATION_PROMPT, HINDI_EXPLANATION_PROMPT
from ai_pipeline.languages import LANGUAGES

class LLMExplanationService:
    def generate_bilingual_explanations(
        self,
        vlm_analysis: str,
        subject: str = "General Science",
        prior_events_context: list = None
    ) -> Dict[str, str]:
        """
        Generates both English and Hindi audio descriptions from VLM analysis.
        Passes prior_events_context to prevent double/over-explaining previously covered diagrams.
        Returns: { "en": "...", "hi": "..." }
        """
        return self.generate_explanations(
            vlm_analysis,
            subject=subject,
            prior_events_context=prior_events_context,
            language_codes=("en", "hi"),
        )

    def generate_explanations(
        self,
        vlm_analysis: str,
        subject: str = "General Science",
        prior_events_context: list = None,
        language_codes=None,
    ) -> Dict[str, str]:
        """Generate narration text for each requested language code."""
        requested = language_codes or LANGUAGES.keys()
        explanations = {}
        for lang in requested:
            if lang not in LANGUAGES:
                continue
            text = self._generate_explanation(
                vlm_analysis, subject, lang=lang,
                prior_events_context=prior_events_context,
            )
            if text:
                explanations[lang] = text
        return explanations

    def _generate_explanation(
        self,
        vlm_analysis: str,
        subject: str,
        lang: str = "en",
        prior_events_context: list = None
    ) -> str:
        if lang == "en":
            prompt = ENGLISH_EXPLANATION_PROMPT.format(analysis=vlm_analysis, subject=subject)
        elif lang == "hi":
            prompt = HINDI_EXPLANATION_PROMPT.format(analysis=vlm_analysis, subject=subject)
        else:
            language_name = LANGUAGES[lang]["name"]
            prompt = f"""
You are an accessibility tutor writing narration for a visually impaired student.
Explain this STEM diagram analysis in {language_name}. Write only in {language_name}, using its native script.

Diagram analysis:
'''{vlm_analysis}'''

Subject: {subject}

Write only 2 or 3 short spoken sentences, with no more than 45 words total. Describe only
labels, parts, and relationships visible in this diagram, and explain its single main point
in plain language. Avoid unnecessary technical terms and concepts not needed to understand
this diagram. Do not preview or hint at later lecture topics. Use only the supplied analysis;
do not add outside facts or assume the student knows material that has not appeared yet.
Return only the narration, without a heading or list.
""".strip()

        if prior_events_context:
            prior_summary = "\n- ".join(prior_events_context[-3:])
            prompt += (
                "\n\nContext of previously described diagram events in this lecture:\n"
                f"- {prior_summary}\n\n"
                "Use earlier descriptions only to avoid repeating what was already explained; do not assume they establish knowledge of later topics. "
                "Explain only the current diagram's visible information. Keep it to 2 or 3 short sentences and no more than 45 words. "
                "Do not preview, predict, or hint at later lecture topics, and do not add concepts just because they appear in the analysis."
            )

        try:
            for text_model in TEXT_MODELS:
                try:
                    response = create_groq_completion(
                        model=text_model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.4
                    )
                    text = clean_thinking_tags(response.choices[0].message.content)
                    if text:
                        return self._limit_narration(text)
                except Exception as e:
                    print(f"Model '{text_model}' error during {lang} explanation generation: {e}")
        except Exception as e:
            print(f"LLM Explanation client error: {e}")

        # Keep fallback narration short and limited to the current diagram.
        if lang == "en":
            return f"This {subject} diagram shows its labeled parts and how they relate. The explanation is limited to what is visible here."
        elif lang == "hi":
            return f"यह {subject} आरेख में नाम दिए गए भाग और उनके आपसी संबंध दिखाता है। विवरण केवल इसी चित्र में दिख रही जानकारी तक सीमित है।"
        return ""

    @staticmethod
    def _limit_narration(text: str, max_sentences: int = 3, max_words: int = 45) -> str:
        """Keep generated speech brief even when a model ignores the prompt limit."""
        cleaned = re.sub(r"\s+", " ", text).strip()
        sentences = [part.strip() for part in re.split(r"(?<=[.!?।؟])\s+", cleaned) if part.strip()]
        concise = " ".join(sentences[:max_sentences])
        words = concise.split()
        if len(words) > max_words:
            concise = " ".join(words[:max_words]).rstrip(" ,;:") + "…"
        return concise
