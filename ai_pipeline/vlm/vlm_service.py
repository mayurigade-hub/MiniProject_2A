import base64
import mimetypes
from pathlib import Path
from typing import Dict, Any
from backend.services.groq_client import create_groq_completion, clean_thinking_tags
from backend.config import VISION_MODELS, TEXT_MODELS

class VLMService:
    def analyze_diagram(self, image_path: str, ocr_text: str = "") -> str:
        """
        Sends diagram image + OCR text context to Groq Vision API.
        If Vision API model fails or is unavailable, falls back to OCR + Text Model analysis.
        """
        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError(f"Diagram image file not found at '{image_path}'")

        with open(path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")
        image_mime_type = mimetypes.guess_type(path.name)[0]
        if image_mime_type not in {"image/jpeg", "image/png", "image/webp"}:
            image_mime_type = "image/jpeg"

        prompt = (
            "Analyze this educational diagram image in detail.\n"
            f"Extracted OCR Text context:\n'''{ocr_text}'''\n\n"
            "Provide a comprehensive technical description including:\n"
            "1. Diagram type (graph, flowchart, schematic, biological diagram, equation, table).\n"
            "2. Structural elements (axes, units, titles, labels, legends, components, trends).\n"
            "3. Key educational takeaway and relationships depicted."
        )

        # Try vision models
        for model_name in VISION_MODELS:
            try:
                response = create_groq_completion(
                    model=model_name,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:{image_mime_type};base64,{base64_image}"}
                                }
                            ]
                        }
                    ],
                    temperature=0.2,
                )
                output = clean_thinking_tags(response.choices[0].message.content)
                if output:
                    return output
            except Exception as e:
                print(f"Vision model '{model_name}' failed: {e}")

        # Fallback to text model + OCR
        text_prompt = f"Analyze diagram based on OCR text:\n{ocr_text}\n{prompt}"
        for text_model in TEXT_MODELS:
            try:
                response = create_groq_completion(
                    model=text_model,
                    messages=[{"role": "user", "content": text_prompt}],
                    temperature=0.3
                )
                output = clean_thinking_tags(response.choices[0].message.content)
                if output:
                    return output
            except Exception as e:
                print(f"Text model '{text_model}' failed: {e}")

        return f"Diagram visual analysis based on available context:\n{ocr_text}"
