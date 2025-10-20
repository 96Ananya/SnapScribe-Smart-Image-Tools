# Use Python 
FROM python:3.11-bullseye


# Install system deps and Tesseract OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libtesseract-dev \
    libleptonica-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (Render provides PORT env)
ENV PORT=10000

# Start using gunicorn
CMD exec gunicorn --bind 0.0.0.0:$PORT app:app
