FROM python:3.9-slim

# Install system dependencies (Tesseract OCR, OpenCV ffmpeg/GL libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose FastAPI backend port
EXPOSE 8000

# Start the FastAPI application. Demo data can be seeded separately with
# `python scripts/seed_data.py` when it is needed.
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
