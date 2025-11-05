# Multi-stage build for FastAPI application
FROM python:3.10-slim as base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for weights and uploads
RUN mkdir -p weights uploads temp results

# Expose port
EXPOSE 9000

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9000"]

