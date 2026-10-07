#!/usr/bin/env python3
"""
diagram_to_speech.py

Pipeline for converting a diagram image into an educational spoken-style explanation and MP3 audio file.

Pipeline steps:
  1. detect_and_understand(): Groq Vision API (or OCR + Groq text model fallback) -> Diagram structural understanding
  2. generate_explanation(): Groq Text API -> 3-5 sentence educational audio explanation
  3. text_to_speech(): gTTS (or pyttsx3 fallback) -> MP3 audio file output
"""

import os
import sys
import re
import base64
import argparse
from pathlib import Path
from dotenv import load_dotenv
from backend.services.groq_client import create_groq_completion, clean_thinking_tags
from backend.config import VISION_MODELS, TEXT_MODELS

# Load environment variables from .env if present
load_dotenv()

def run_ocr_fallback(image_path: str) -> str:
    """Runs pytesseract OCR on the image to extract raw text as a fallback."""
    print("   [Fallback] Performing OCR with pytesseract...")
    try:
        import pytesseract
        from PIL import Image
    except ImportError as e:
        raise ImportError(
            "Error: pytesseract or Pillow missing for OCR fallback. "
            "Install via 'pip install pytesseract pillow'."
        ) from e

    try:
        img = Image.open(image_path)
        ocr_text = pytesseract.image_to_string(img).strip()
        if not ocr_text:
            print("   [Fallback] OCR extracted empty text.")
            return "No readable text found via OCR."
        print(f"   [Fallback] Extracted {len(ocr_text)} characters via OCR.")
        return ocr_text
    except Exception as e:
        print(f"   [Fallback] OCR failed: {e}")
        return f"OCR processing failed: {e}"


def detect_and_understand(image_path: str) -> str:
    """
    STEP 1: Diagram Understanding via Groq API.
    Attempts to send image directly to a Groq Vision model.
    If Vision API is unavailable or fails, falls back to OCR + Groq Text model.
    """
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Error: Diagram image file not found at '{image_path}'")

    print(f"\n[Step 1/3] Analyzing diagram: {image_path}...")
    # Read and encode image
    with open(path, "rb") as img_file:
        base64_image = base64.b64encode(img_file.read()).decode("utf-8")

    vision_prompt = (
        "Analyze this diagram image in detail. Identify and describe:\n"
        "1. Diagram type (e.g. line graph, bar chart, flowchart, schematic, table).\n"
        "2. Key elements (axes, labels, titles, data series, colors, components, icons).\n"
        "3. Relationships, trends, and overall meaning depicted in the diagram."
    )

    # Attempt Vision-capable models
    for model_name in VISION_MODELS:
        try:
            print(f" -> Attempting Groq Vision model '{model_name}'...")
            response = create_groq_completion(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": vision_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                },
                            },
                        ],
                    }
                ],
                temperature=0.2,
            )
            raw_output = response.choices[0].message.content
            understanding = clean_thinking_tags(raw_output)
            if understanding:
                print(" -> Successfully analyzed diagram using Vision API.")
                return understanding
        except Exception as e:
            print(f" -> Vision model '{model_name}' unavailable or error: {e}")

    # Fallback: OCR + Groq Text model
    print(" -> Vision model unavailable. Falling back to OCR + Groq Text model...")
    ocr_text = run_ocr_fallback(image_path)
    text_prompt = (
        f"The following text was extracted via OCR from a diagram image:\n"
        f"'''\n{ocr_text}\n'''\n\n"
        f"Based on this OCR text, infer and describe:\n"
        f"1. Likely diagram type and structure.\n"
        f"2. Key elements, axes, labels, or concepts identified.\n"
        f"3. Overall meaning and relationships shown in the diagram."
    )

    for text_model in TEXT_MODELS:
        try:
            print(f" -> Attempting Groq Text model '{text_model}' with OCR input...")
            response = create_groq_completion(
                model=text_model,
                messages=[{"role": "user", "content": text_prompt}],
                temperature=0.3,
            )
            raw_output = response.choices[0].message.content
            understanding = clean_thinking_tags(raw_output)
            if understanding:
                print(" -> Successfully generated diagram understanding via OCR + Text model.")
                return understanding
        except Exception as e:
            print(f" -> Text model '{text_model}' error: {e}")

    raise RuntimeError("Error: Failed to process diagram with both Vision and OCR text fallbacks.")


def generate_explanation(understanding_text: str) -> str:
    """
    STEP 2: Educational Explanation Generation via Groq API.
    Takes Step 1 analysis and converts it into a spoken-style educational explanation.
    """
    print("\n[Step 2/3] Generating educational spoken explanation...")
    prompt = (
        "You are an educational tutor creating an audio narrative for a student.\n"
        "Based on the following technical breakdown of a diagram:\n"
        f"'''\n{understanding_text}\n'''\n\n"
        "Generate a clear, engaging, spoken-style educational explanation that a student can listen to and understand fully.\n"
        "DO NOT write a generic caption like 'there is a graph'.\n"
        "Explain what the diagram shows, key data points or components, and what it means conceptually.\n"
        "Keep the explanation strictly between 3 to 5 clear sentences, written for smooth text-to-speech audio reading."
    )

    for text_model in TEXT_MODELS:
        try:
            print(f" -> Requesting explanation from '{text_model}'...")
            response = create_groq_completion(
                model=text_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
            )
            raw_output = response.choices[0].message.content
            explanation = clean_thinking_tags(raw_output)
            if explanation:
                print(" -> Educational explanation generated successfully.")
                return explanation
        except Exception as e:
            print(f" -> Model '{text_model}' error: {e}")

    raise RuntimeError("Error: Failed to generate educational explanation from Groq API.")


def text_to_speech(explanation_text: str, output_path: str = "output_audio.mp3") -> str:
    """
    STEP 3: Text-to-Speech synthesis.
    Converts explanation text to an MP3 audio file using gTTS.
    Falls back to pyttsx3 if offline or if gTTS fails.
    """
    print(f"\n[Step 3/3] Synthesizing audio to '{output_path}'...")
    abs_output_path = str(Path(output_path).resolve())

    # Try gTTS (online, natural sounding)
    try:
        from gtts import gTTS
        print(" -> Synthesizing audio via gTTS...")
        tts = gTTS(text=explanation_text, lang="en")
        tts.save(abs_output_path)
        print(" -> Audio file successfully saved using gTTS.")
        return abs_output_path
    except Exception as gtts_error:
        print(f" -> gTTS synthesis failed or offline: {gtts_error}")
        print(" -> Falling back to pyttsx3 offline engine...")

    # Fallback to pyttsx3 (offline)
    try:
        import pyttsx3
        engine = pyttsx3.init()
        # Save as wav if mp3 saving isn't supported natively on pyttsx3 platform
        fallback_path = abs_output_path if abs_output_path.endswith(".mp3") else abs_output_path + ".mp3"
        engine.save_to_file(explanation_text, fallback_path)
        engine.runAndWait()
        print(" -> Audio file successfully saved using pyttsx3 offline fallback.")
        return fallback_path
    except Exception as pyttsx3_error:
        raise RuntimeError(
            f"Error: Both gTTS and pyttsx3 audio synthesis failed.\n"
            f"gTTS error: {gtts_error}\n"
            f"pyttsx3 error: {pyttsx3_error}"
        ) from pyttsx3_error


def main():
    parser = argparse.ArgumentParser(
        description="diagram_to_speech.py: Turn diagram images into educational spoken audio explanations."
    )
    parser.add_argument(
        "image_path",
        type=str,
        help="Path to the diagram image file (e.g. path/to/diagram.jpg)"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="output_audio.mp3",
        help="Path for output audio MP3 file (default: output_audio.mp3)"
    )

    args = parser.parse_args()

    try:
        # Step 1: Diagram understanding
        understanding = detect_and_understand(args.image_path)

        # Step 2: Educational explanation
        explanation = generate_explanation(understanding)

        # Step 3: Text-to-speech
        audio_file_path = text_to_speech(explanation, args.output)

        # Step 4: CLI output
        print("\n" + "=" * 60)
        print("GENERATED EDUCATIONAL EXPLANATION:")
        print("=" * 60)
        print(explanation)
        print("=" * 60)
        print(f"\nAUDIO FILE SAVED AT: {audio_file_path}")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\nPipeline Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
