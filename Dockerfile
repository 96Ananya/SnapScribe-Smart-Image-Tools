# Use Python slim image
FROM python:3.11-slim

# Install system deps and tesseract
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy project files
COPY . /app

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Render provides PORT env)
ENV PORT 10000
# Use gunicorn for production
CMD exec gunicorn --bind 0.0.0.0:$PORT app:app
