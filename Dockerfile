FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for xhtml2pdf and its dependencies (cairo, pango)
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    pkg-config \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p data templates

# Copy application code
COPY . .

# Expose the port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]
