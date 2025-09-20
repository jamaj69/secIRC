# secIRC Dockerfile for Testing
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY config/ ./config/
COPY test_data/ ./test_data/
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p logs data temp uploads

# Set environment variables
ENV PYTHONPATH=/app/src
ENV SECIRC_ENV=test
ENV SECIRC_DEBUG=true
ENV SECIRC_LOG_LEVEL=INFO

# Expose ports
EXPOSE 6667 6697

# Default command (can be overridden)
CMD ["python", "src/server/main.py"]
