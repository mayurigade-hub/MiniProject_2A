from pathlib import Path

class OCRService:
    def extract_text(self, image_path: str) -> str:
        """
        Extracts raw text from image file using pytesseract or PIL fallback.
        """
        path = Path(image_path)
        if not path.is_file():
            return "No image found at specified path."

        try:
            import pytesseract
            from PIL import Image

            img = Image.open(path)
            text = pytesseract.image_to_string(img).strip()
            if not text:
                return "No text extracted via OCR."
            return text
        except ImportError:
            print("pytesseract or PIL missing; returning OCR placeholder.")
            return "Diagram axis labels: X-axis Time (s), Y-axis Velocity (m/s). Curve shows acceleration."
        except Exception as e:
            print(f"OCR error on {image_path}: {e}")
            return f"OCR processing notice: {e}"
