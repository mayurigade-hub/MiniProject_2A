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

Write 3 to 5 concise, natural spoken sentences. Explain the diagram's useful relationships,
labels, trends, and educational meaning. Do not add unsupported details. Keep standard
scientific terms when they are commonly used in English, but make the explanation fluent
and easy to understand when spoken in {language_name}. Return only the narration.
""".strip()

        if prior_events_context:
            prior_summary = "\n- ".join(prior_events_context[-3:])
            prompt += (
                "\n\nContext of previously described diagram events in this lecture:\n"
                f"- {prior_summary}\n\n"
                "CRITICAL INSTRUCTION: DO NOT re-explain or over-explain diagram concepts, labels, or structures already described above. "
                "Focus exclusively on the NEW visual relationships, specific data trends, or structural changes introduced at this timestamp."
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
                        return text
                except Exception as e:
                    print(f"Model '{text_model}' error during {lang} explanation generation: {e}")
        except Exception as e:
            print(f"LLM Explanation client error: {e}")

        # Dynamic, context-grounded fallback explanations if Groq API fails or is rate-limited
        summary_snippet = ""
        if vlm_analysis:
            # Extract first 200 non-empty characters for grounded context
            clean_lines = [line.strip() for line in vlm_analysis.splitlines() if line.strip() and not line.startswith("VLM")]
            if clean_lines:
                summary_snippet = " ".join(clean_lines[:2])

        if lang == "en":
            if summary_snippet:
                return (
                    f"This {subject} diagram visualizes key instructional concepts: {summary_snippet[:160]}. "
                    "The components and trends labeled in the figure highlight core educational principles of this topic."
                )
            return (
                f"This {subject} diagram illustrates key technical concepts. "
                "The visual layout displays data trends and structural components clearly labeled. "
                "Understanding these relationships highlights the fundamental principles of the topic."
            )
        elif lang == "hi":
            if summary_snippet:
                return (
                    f"यह {subject} आरेख मुख्य अवधारणाओं को प्रस्तुत करता है: {summary_snippet[:160]}। "
                    "चित्र में दिए गए मुख्य घटक और डेटा बिंदु इस विषय के मूलभूत सिद्धांतों को स्पष्ट रूप से दर्शाते हैं।"
                )
            return (
                f"यह {subject} आरेख मुख्य तकनीकी अवधारणाओं को दर्शाता है। "
                "दृश्य लेआउट डेटा प्रवृत्तियों और संरचनात्मक घटकों को स्पष्ट रूप से प्रस्तुत करता है। "
                "इन संबंधों को समझना इस विषय के मूलभूत सिद्धांतों को उजागर करता है।"
            )
        return ""
